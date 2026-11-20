variable "environment" {
  description = "Target deployment environment"
  type        = string
  default     = "production"
}

variable "aws_region" {
  description = "Primary AWS Cloud Region"
  type        = string
  default     = "us-east-1"
}

variable "aws_instance_type" {
  description = "EC2 Instance type for primary compute"
  type        = string
  default     = "t3.medium"
}

variable "azure_region" {
  description = "Secondary Azure Cloud Region for DR"
  type        = string
  default     = "East US 2"
}

variable "azure_vm_size" {
  description = "Azure VM SKU size for standby compute"
  type        = string
  default     = "Standard_B2s"
}
