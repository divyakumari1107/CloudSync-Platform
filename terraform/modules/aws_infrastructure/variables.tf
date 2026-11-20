variable "aws_region" {
  type        = string
  description = "AWS Region"
}

variable "environment" {
  type        = string
  description = "Environment identifier"
}

variable "instance_type" {
  type        = string
  description = "EC2 instance size"
}

variable "s3_bucket_prefix" {
  type        = string
  description = "Prefix for S3 storage bucket"
}
