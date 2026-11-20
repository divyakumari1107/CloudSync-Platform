# Resource Group
resource "azurerm_resource_group" "secondary_rg" {
  name     = "rg-cloudsync-${var.environment}"
  location = var.azure_region

  tags = {
    Project     = "CloudSync-MultiCloud-DR"
    Environment = var.environment
  }
}

# Virtual Network & Subnet
resource "azurerm_virtual_network" "vnet" {
  name                = "vnet-cloudsync-azure"
  address_space       = ["10.200.0.0/16"]
  location            = azurerm_resource_group.secondary_rg.location
  resource_group_name = azurerm_resource_group.secondary_rg.name
}

resource "azurerm_subnet" "subnet" {
  name                 = "snet-standby-compute"
  resource_group_name  = azurerm_resource_group.secondary_rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.200.1.0/24"]
}

# Network Security Group
resource "azurerm_network_security_group" "nsg" {
  name                = "nsg-cloudsync-azure-vm"
  location            = azurerm_resource_group.secondary_rg.location
  resource_group_name = azurerm_resource_group.secondary_rg.name

  security_rule {
    name                       = "AllowHTTP"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "AllowAppPort"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "7002"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "AllowSSH"
    priority                   = 120
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}

# Public IP & NIC
resource "azurerm_public_ip" "pip" {
  name                = "pip-cloudsync-azure-standby"
  location            = azurerm_resource_group.secondary_rg.location
  resource_group_name = azurerm_resource_group.secondary_rg.name
  allocation_method   = "Static"
  sku                 = "Standard"
}

resource "azurerm_network_interface" "nic" {
  name                = "nic-cloudsync-azure-standby"
  location            = azurerm_resource_group.secondary_rg.location
  resource_group_name = azurerm_resource_group.secondary_rg.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.subnet.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.pip.id
  }
}

resource "azurerm_network_interface_security_group_association" "nic_nsg_assoc" {
  network_interface_id      = azurerm_network_interface.nic.id
  network_security_group_id = azurerm_network_security_group.nsg.id
}

# Azure Linux Virtual Machine (Secondary Standby)
resource "azurerm_linux_virtual_machine" "standby_vm" {
  name                = "vm-cloudsync-azure-standby"
  resource_group_name = azurerm_resource_group.secondary_rg.name
  location            = azurerm_resource_group.secondary_rg.location
  size                = var.vm_size
  admin_username      = "cloudsyncadmin"

  network_interface_ids = [
    azurerm_network_interface.nic.id,
  ]

  admin_ssh_key {
    username   = "cloudsyncadmin"
    public_key = fileexists("~/.ssh/id_rsa.pub") ? file("~/.ssh/id_rsa.pub") : "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGENERATEDSTANDBYKEYFORCLOUDSYNC cloudsyncadmin@azure"
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "StandardSSD_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }

  tags = {
    Role = "SecondaryStandby"
    Region = var.azure_region
  }
}

# Azure Blob Storage Account for Disaster Recovery Storage
resource "azurerm_storage_account" "dr_storage" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.secondary_rg.name
  location                 = azurerm_resource_group.secondary_rg.location
  account_tier             = "Standard"
  account_replication_type = "GRS" # Geo-Redundant Storage

  tags = {
    Environment = var.environment
    Purpose     = "CrossCloudObjectReplica"
  }
}

resource "azurerm_storage_container" "dr_container" {
  name                  = "cloudsync-backup-vault"
  storage_account_name  = azurerm_storage_account.dr_storage.name
  container_access_type = "private"
}

# Azure Monitor Alert for High Latency & Failover Detection
resource "azurerm_monitor_metric_alert" "azure_standby_alert" {
  name                = "alert-cloudsync-standby-health"
  resource_group_name = azurerm_resource_group.secondary_rg.name
  scopes              = [azurerm_linux_virtual_machine.standby_vm.id]
  description         = "Triggers when Standby Azure VM takes over active traffic"
  severity            = 1
  frequency           = "PT1M"
  window_size         = "PT5M"

  criteria {
    metric_namespace = "Microsoft.Compute/virtualMachines"
    metric_name      = "Percentage CPU"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 85
  }
}
