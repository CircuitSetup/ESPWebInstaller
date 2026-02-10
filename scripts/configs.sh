#!/bin/bash

# Metadata for each YAML config: "Display Name|MCU Type"
declare -A CONFIG_META

CONFIG_META["circuitsetup-gdo-default.yaml"]="CircuitSetup Security+ Garage Door Opener|ESP32_S3"
CONFIG_META["circuitsetup-gdo-dry-contact.yaml"]="CircuitSetup Garage Door Opener Dry Contact|ESP32_S3"

CONFIG_META["6chan_energy_meter_main_board.yaml"]="CircuitSetup 6 Channel Energy Meter Main|ESP32"
CONFIG_META["6chan_energy_meter_1-addon.yaml"]="CircuitSetup 6 Channel Energy Meter Main + 1 Add-on|ESP32"
CONFIG_META["6chan_energy_meter_2-addons.yaml"]="CircuitSetup 6 Channel Energy Meter Main + 2 Add-ons|ESP32"
CONFIG_META["6chan_energy_meter_3-addons.yaml"]="CircuitSetup 6 Channel Energy Meter Main + 3 Add-ons|ESP32"
CONFIG_META["6chan_energy_meter_3-addons_2-voltages.yaml"]="CircuitSetup 6 Channel Energy Meter 3 Add-ons 2 Voltages|ESP32"
CONFIG_META["6chan_energy_meter_4-addons.yaml"]="CircuitSetup 6 Channel Energy Meter Main + 4 Add-ons|ESP32"
CONFIG_META["6chan_energy_meter_5-addons.yaml"]="CircuitSetup 6 Channel Energy Meter Main + 5 Add-ons|ESP32"
CONFIG_META["6chan_energy_meter_6-addons.yaml"]="CircuitSetup 6 Channel Energy Meter Main + 6 Add-ons|ESP32"

CONFIG_META["6chan_energy_meter_main_ethernet.yaml"]="CircuitSetup 6 Channel Energy Meter Ethernet|ESP32_S3"
CONFIG_META["6chan_energy_meter_main_ethernet_waveshare.yaml"]="CircuitSetup 6 Channel Energy Meter Ethernet Waveshare|ESP32_S3"
CONFIG_META["6chan_energy_meter_1-addon_ethernet.yaml"]="CircuitSetup 6 Channel Energy Meter + 1 Add-on Ethernet|ESP32_S3"
CONFIG_META["6chan_energy_meter_1-addon_ethernet_waveshare.yaml"]="CircuitSetup 6 Channel Energy Meter + 1 Add-on Ethernet Waveshare|ESP32_S3"
CONFIG_META["6chan_energy_meter_2-addons_ethernet.yaml"]="CircuitSetup 6 Channel Energy Meter + 2 Add-ons Ethernet|ESP32_S3"
CONFIG_META["6chan_energy_meter_2-addons_ethernet_waveshare.yaml"]="CircuitSetup 6 Channel Energy Meter + 2 Add-ons Ethernet Waveshare|ESP32_S3"
CONFIG_META["6chan_energy_meter_3-addons_ethernet.yaml"]="CircuitSetup 6 Channel Energy Meter + 3 Add-ons Ethernet|ESP32_S3"
CONFIG_META["6chan_energy_meter_3-addons_ethernet_waveshare.yaml"]="CircuitSetup 6 Channel Energy Meter + 3 Add-ons Ethernet Waveshare|ESP32_S3"
CONFIG_META["6chan_energy_meter_4-addons_ethernet.yaml"]="CircuitSetup 6 Channel Energy Meter + 4 Add-ons Ethernet|ESP32_S3"
CONFIG_META["6chan_energy_meter_4-addons_ethernet_waveshare.yaml"]="CircuitSetup 6 Channel Energy Meter + 4 Add-ons Ethernet Waveshare|ESP32_S3"
CONFIG_META["6chan_energy_meter_5-addons_ethernet.yaml"]="CircuitSetup 6 Channel Energy Meter + 5 Add-ons Ethernet|ESP32_S3"
CONFIG_META["6chan_energy_meter_5-addons_ethernet_waveshare.yaml"]="CircuitSetup 6 Channel Energy Meter + 5 Add-ons Ethernet Waveshare|ESP32_S3"
CONFIG_META["6chan_energy_meter_6-addons_ethernet.yaml"]="CircuitSetup 6 Channel Energy Meter + 6 Add-ons Ethernet|ESP32_S3"
CONFIG_META["6chan_energy_meter_6-addons_ethernet_waveshare.yaml"]="CircuitSetup 6 Channel Energy Meter + 6 Add-ons Ethernet Waveshare|ESP32_S3"

# Flat list of config file names
CONFIG_LIST=("${!CONFIG_META[@]}")
