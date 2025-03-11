# User Limit Module

## Overview
The User Limit module for Odoo allows administrators to set a maximum limit on the number of internal users that can be created in the system. This is useful for controlling licensing costs and ensuring compliance with user-based licensing agreements.

## Features
- Set a maximum number of internal users allowed in the system
- Automatically prevents creation of new users when the limit is reached
- Only one configuration can be active at a time
- Simple and intuitive user interface
- Detailed logging for troubleshooting

## Installation
1. Place the module in your Odoo addons directory
2. Update the module list in Odoo
3. Install the module through the Odoo interface

## Configuration
1. Navigate to **Settings > Users > User Limit Configurations**
2. Create a new configuration or edit an existing one
3. Set the maximum number of users allowed
4. Activate the configuration by clicking the "Activate" button

## Usage
Once configured, the module automatically enforces the user limit:
- When creating new users, the system checks if the limit would be exceeded
- If the limit would be exceeded, an error message is displayed and the user creation is blocked
- Portal and public users are not counted against the limit

## Technical Details

### Models
- `res.user.limit.config`: Stores the user limit configurations
- `res.users`: Extended to check against the limit when creating new users

### Methods
- `get_user_limit()`: Returns the current user limit from the active configuration
- `toggle_active()`: Ensures only one configuration is active at a time

### Constraints
- Only one configuration can be active at a time
- Maximum users must be greater than 0 and less than 100,000
- Configuration names must be unique

## Troubleshooting
- Check the server logs for detailed information about user limit enforcement
- Ensure that only one configuration is active
- If no configuration is active, user creation is unlimited

## License
This module is licensed under the LGPL-3 license.

## Author
Alvin Paul L. Azurin

## Support
For support, please contact the author or visit [Cre8or Lab](https://www.cre8or-lab.com).
