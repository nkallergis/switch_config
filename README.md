# Ugly tool to create Cisco switch configurations
## Usage
- Create generic or interface-specific templates per software flavor (NXOS, IOS etc)
- Create a CSV file per switch that contains details for the switch in general and on a per-interface base too (example __"switchB52.csv"__)
- Declare the list of CSV files in __switch_config.py__ variable *new_switch_list*
- In case of migration, be sure that the source configuration file (named exactly as in the CSV) exists in the same folder as __switch_config.py__

## Examples
Examples exist in the __"switchB52.csv"__ file for all implemented uses (uplink, server, user, migration)
