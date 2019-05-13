#! /usr/bin/env python
import csv
import re
from jinja2 import Template

################################################################################
# GENERIC VARIABLES
################################################################################
new_switch_list = ['switchB52']
new_switch_configuration_file_suffix = '.config.txt'
new_switch_details_file_suffix = '.csv'
new_switch_details_firstinterfacerow = 8

generic_template_file_suffix = '.generic_template.j2'
interface_template_file_suffix = '.interface_template.j2'

################################################################################
# FUNCTIONS DEFINITION
################################################################################
def migrate_port(new_port, old_port, conf_file, description=None):
  # Read the configuration file into old_configuration
  with open(conf_file) as old_configuration_file:
    old_configuration = old_configuration_file.read()
  
  # Extract the section about the old_port, rename the port to new_port
  interface_pattern = '(interface ' + old_port + '[\s\S]*?!)'
  interface_configuration = re.findall(interface_pattern, old_configuration)[0]
  interface_configuration = '\r\n' + interface_configuration.replace(old_port, new_port)
  
  if description:
    description_pattern = '(description.*)'
    new_description = 'description ' + description
    old_description = re.findall(description_pattern, interface_configuration)
    if len(old_description) > 0:
      interface_configuration = interface_configuration.replace(old_description[0], new_description)
    else:
      interface_configuration = re.sub('(interface.*\r\n)', r'\1 ' + new_description + '\r\n', interface_configuration)
  return(interface_configuration)

def migrate_ios2nxos(configuration):
  # REMOVE COMMANDS
  configuration = configuration.replace('\r\n switchport nonegotiate', '')
  configuration = configuration.replace('\r\n logging event spanning-tree', '')
  configuration = configuration.replace('\r\n no mdix auto', '')
  configuration = configuration.replace('\r\n switchport trunk encapsulation dot1q', '')
  configuration = configuration.replace('\r\n channel-protocol lacp', '')

  # CHANGE COMMANDS
  configuration = configuration.replace('logging event status', 'logging event port link-status')
  configuration = configuration.replace('logging event link-status', 'logging event port link-status')
  configuration = configuration.replace('logging event trunk-status', 'logging event port trunk-status')

  # ADD COMMANDS
  configuration = re.sub('(interface.*\r\n)', r'\1 no shutdown\r\n', configuration)
  configuration = re.sub('(interface.*\r\n)', r'\1 switchport\r\n', configuration)
  return(configuration)

def extract_vlans(conf):
  vlans_string = ''
  vlans_list = []
  for line in conf.splitlines():
    vlan_pattern = 'vlan '
    vlans = line.split(vlan_pattern)
    if len(vlans) > 1:
      # print(vlans[1])
      vlans_string += vlans[1] + ','
  vlans_list = vlans_string.split(',')
  vlans_list = set(vlans_list)
  vlans_string = ''
  for vlan in vlans_list:
    vlans_string += vlan + ','
  return(vlans_string)

################################################################################
# MAIN FUNCTION
################################################################################
for new_switch in new_switch_list:
  
  # INITIALIZE NEW SWITCH CONFIGURATION
  new_switch_configuration = ''

  # READ CSV FILE CONTAINING NEW SWITCH DETAILS
  with open(new_switch + new_switch_details_file_suffix) as new_switch_details_file:
    new_switch_details = csv.reader(new_switch_details_file, delimiter=';')
    line_count = 1
    for new_switch_details_row in new_switch_details:

      # READ GENERIC SWITCH ATTRIBUTES
      if line_count == 1:
        config_type = new_switch_details_row[1]
      if line_count == 2:
        hostname = new_switch_details_row[1]
      elif line_count == 3:
        vtp_mode = new_switch_details_row[1]
      elif line_count == 4:
        mgmt_ip = new_switch_details_row[1]
      elif line_count == 5:
        software = new_switch_details_row[1]

      # CREATE NEW SWITCH GENERIC CONFIGURATION
      elif line_count == 6:
        if config_type.lower() == 'full':
          with open(software + generic_template_file_suffix) as t:
            generic_config_template = Template(t.read())
          new_switch_configuration += generic_config_template.render(hostname=hostname,mgmt_ip=mgmt_ip,vtp_mode=vtp_mode)
        with open(software + interface_template_file_suffix) as t:
          interface_config_template = Template(t.read())

      # READ ROW (INTERFACE) VALUES
      elif line_count >= new_switch_details_firstinterfacerow:
        new_port = new_switch_details_row[0]
        usage = new_switch_details_row[1]
        info1 = new_switch_details_row[2]
        info2 = new_switch_details_row[3]
        description = new_switch_details_row[4]
        
        # CREATE NEW INTERFACE CONFIGURATION
        if usage.lower() == 'migration':
          new_switch_configuration += migrate_port(new_port, info1, info2, description)
        else:
          new_switch_configuration += interface_config_template.render(if_name=new_port,if_use=usage,if_info1=info1,if_info2=info2,description=description)
            
      line_count += 1

  new_switch_configuration = migrate_ios2nxos(new_switch_configuration)

  with open(new_switch + new_switch_configuration_file_suffix, 'w') as new_switch_configuration_file:
          new_switch_configuration_file.write(new_switch_configuration)

  # vlans_to_add = extract_vlans(interfaces_configuration)
  # print('\r\nVLANs to add on ' + switch + ':')
  # print(vlans_to_add)
