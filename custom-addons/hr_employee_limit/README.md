# HR Employee Limit

## Overview
This Odoo module adds a constraint to limit the number of employees that can be created in the system. Once the configured limit is reached, no new employees can be created.

## Features
- Configure maximum employee limit through a dedicated configuration interface
- Only one configuration can be active at a time
- Automatically prevents creation of new employees when the limit is reached
- Provides clear error messages when attempting to exceed the limit
- Unlimited employees allowed when no configuration is enabled

## Installation
1. Copy the module to your Odoo addons directory
2. Update the module list in Odoo
3. Install the module from the Apps menu

## Configuration
1. Navigate to **Employees > Configuration > Employee Limit**
2. Create a new configuration with your desired employee limit
3. Activate the configuration by clicking the "Active" button
4. Only one configuration can be active at a time - activating a new configuration will automatically deactivate any previously active ones

## Usage
Once configured, the module will automatically enforce the employee limit:

1. When creating a new employee, the system checks if the limit has been reached
2. If the limit is reached, a clear error message is displayed
3. To increase the limit, simply update the active configuration
4. To remove the limit, deactivate all configurations

## Technical Details
- The module uses the `hr_employee_limit_config` model to store configurations
- Each configuration has a maximum employee count and an active state
- The active state is controlled by two fields:
  - `active`: Controls visibility in the UI (standard Odoo behavior)
  - `is_enabled`: Controls whether the configuration is used for limit enforcement
- Only one configuration can be active and enabled at a time

## Dependencies
- Human Resources (`hr`) module

## License
This module is licensed under LGPL-3.

## Author
Alvin Paul L. Azurin

## Website
https://www.cre8or-lab.com
