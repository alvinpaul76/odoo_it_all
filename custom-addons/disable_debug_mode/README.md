# Disable Debug Mode for Non-Admin Users

## Overview
This Odoo module restricts access to debug mode, allowing only administrator users to use this feature. It prevents non-admin users from accessing debug mode even if they manually add `?debug=1` to the URL.

## Features
- Restricts debug mode access to users with administrator privileges only
- Automatically redirects non-admin users attempting to access debug mode
- Preserves all other URL parameters during redirection
- Maintains full debug functionality for admin users
- Logs attempted unauthorized access to debug mode for security monitoring

## Technical Implementation
The module works through two main mechanisms:

1. **HTTP Request Interception**: Intercepts all HTTP requests to check for debug parameters. If a non-admin user tries to access debug mode, they're redirected to the same page without the debug parameter.

2. **Session Info Override**: Overrides the session information endpoint to ensure debug mode is disabled for non-admin users in the session data sent to the client.

Key components:
- Custom `ir.http` model that extends Odoo's HTTP handling
- User permission checking based on the 'base.group_system' security group
- Clean URL parameter handling to maintain other parameters during redirection
- Comprehensive logging of all debug mode access attempts

## Installation
1. Copy the module to your Odoo addons directory
2. Update the module list in Odoo
3. Install the module from the Apps menu

## Configuration
No configuration is needed. The module works automatically after installation.

## Troubleshooting
If you encounter any issues, check the Odoo server logs for messages related to debug mode access. The module includes detailed logging that can help identify problems.

Common log messages:
- "Debug mode requested via URL parameter" - Indicates a user is trying to access debug mode
- "Debug access check - User: X, Is Admin: True/False" - Shows the user and their admin status
- "Non-admin user X attempted to access debug mode - redirecting" - Indicates a non-admin user was redirected

## Security Considerations
This module enhances security by preventing non-admin users from accessing debug mode, which could expose sensitive information or allow them to perform actions they shouldn't have access to.

## Compatibility
This module is compatible with Odoo 15.0 and above.

## License
This module is licensed under LGPL-3.

## Author
Alvin Paul L. Azurin

## Website
https://www.cre8or-lab.com
