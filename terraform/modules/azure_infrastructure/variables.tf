variable "azure_region" {
  type        = string
  description = "Target Azure Region"
}

variable "environment" {
  type        = string
  description = "Target Environment"
}

variable "vm_size" {
  type        = string
  description = "Azure VM Size SKU"
}

variable "storage_account_name" {
  type        = string
  description = "Unique name for Azure storage account"
}
