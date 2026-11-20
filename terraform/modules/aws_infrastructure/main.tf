# AWS VPC and Networking
resource "aws_vpc" "primary_vpc" {
  cidr_block           = "10.100.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "cloudsync-aws-vpc-${var.environment}"
  }
}

resource "aws_subnet" "primary_public_subnet" {
  vpc_id                  = aws_vpc.primary_vpc.id
  cidr_block              = "10.100.1.0/24"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true

  tags = {
    Name = "cloudsync-aws-public-subnet"
  }
}

resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.primary_vpc.id

  tags = {
    Name = "cloudsync-aws-igw"
  }
}

resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.primary_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }

  tags = {
    Name = "cloudsync-aws-public-rt"
  }
}

resource "aws_route_table_association" "public_assoc" {
  subnet_id      = aws_subnet.primary_public_subnet.id
  route_table_id = aws_route_table.public_rt.id
}

# Security Group
resource "aws_security_group" "primary_sg" {
  name        = "cloudsync-aws-node-sg"
  description = "Allow HTTP, HTTPS, SSH and CloudWatch agent"
  vpc_id      = aws_vpc.primary_vpc.id

  ingress {
    description = "HTTP Traffic from Nginx Ingress"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "App Port"
    from_port   = 7001
    to_port     = 7001
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH for Ansible Automation"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# AWS EC2 Instance
resource "aws_instance" "primary_node" {
  ami           = "ami-0c7217cdde317cfec" # Ubuntu 22.04 LTS HVM
  instance_type = var.instance_type
  subnet_id     = aws_subnet.primary_public_subnet.id
  vpc_security_group_ids = [aws_security_group.primary_sg.id]

  root_block_device {
    volume_size           = 30
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }

  user_data = <<-EOF
              #!/bin/bash
              apt-get update -y
              apt-get install -y nginx python3-pip
              echo "CloudSync AWS Primary Node active in ${var.aws_region}" > /var/www/html/index.html
              EOF

  tags = {
    Name = "cloudsync-aws-primary-ec2"
    Role = "PrimaryActive"
  }
}

# S3 Storage Bucket for Object Replication
resource "aws_s3_bucket" "replication_vault" {
  bucket_prefix = var.s3_bucket_prefix
  force_destroy = true

  tags = {
    Name = "cloudsync-primary-s3-vault"
  }
}

resource "aws_s3_bucket_versioning" "vault_versioning" {
  bucket = aws_s3_bucket.replication_vault.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "vault_encryption" {
  bucket = aws_s3_bucket.replication_vault.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# CloudWatch Metric Alarm for EC2 Health & Automated Failover
resource "aws_cloudwatch_metric_alarm" "primary_health_alarm" {
  alarm_name          = "cloudsync-aws-primary-unhealthy"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "StatusCheckFailed"
  namespace           = "AWS/EC2"
  period              = 60
  statistic           = "Maximum"
  threshold           = 0
  alarm_description   = "Triggers Ansible failover playbook when AWS EC2 StatusCheck fails"

  dimensions = {
    InstanceId = aws_instance.primary_node.id
  }
}
