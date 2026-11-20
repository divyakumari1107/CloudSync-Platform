output "aws_ec2_public_ip" {
  description = "Public IP of Primary AWS EC2 Instance"
  value       = module.aws_primary.ec2_public_ip
}

output "aws_s3_bucket" {
  description = "Name of Primary AWS S3 Replication Bucket"
  value       = module.aws_primary.s3_bucket_name
}

output "azure_vm_public_ip" {
  description = "Public IP of Standby Azure VM Instance"
  value       = module.azure_secondary.vm_public_ip
}

output "azure_blob_endpoint" {
  description = "Primary Blob Storage Endpoint in Azure"
  value       = module.azure_secondary.blob_endpoint
}

output "cloudwatch_alarm_arn" {
  description = "ARN of AWS CloudWatch Health & Latency Alarm"
  value       = module.aws_primary.cloudwatch_alarm_arn
}

output "azure_monitor_alert_id" {
  description = "Resource ID of Azure Monitor Standby Alert"
  value       = module.azure_secondary.azure_monitor_alert_id
}
