output "vm_id" {
  value = azurerm_linux_virtual_machine.standby_vm.id
}

output "vm_public_ip" {
  value = azurerm_public_ip.pip.ip_address
}

output "storage_account_name" {
  value = azurerm_storage_account.dr_storage.name
}

output "blob_endpoint" {
  value = azurerm_storage_account.dr_storage.primary_blob_endpoint
}

output "azure_monitor_alert_id" {
  value = azurerm_monitor_metric_alert.azure_standby_alert.id
}
