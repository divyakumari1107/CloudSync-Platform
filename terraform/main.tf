terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = "CloudSync-MultiCloud-DR"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

provider "azurerm" {
  features {}
}

module "aws_primary" {
  source           = "./modules/aws_infrastructure"
  aws_region       = var.aws_region
  environment      = var.environment
  instance_type    = var.aws_instance_type
  s3_bucket_prefix = "cloudsync-primary-vault"
}

module "azure_secondary" {
  source              = "./modules/azure_infrastructure"
  azure_region        = var.azure_region
  environment         = var.environment
  vm_size             = var.azure_vm_size
  storage_account_name = "cloudsyncvaultbackup"
}
