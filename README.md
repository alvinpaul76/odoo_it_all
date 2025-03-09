# Odoo It All

A collection of tools to help with Odoo development and deployment.

## Features

- Fresh installation of Odoo modules without demo data
- Configurable module installation through environment variables
- Custom addons path support
- Database management utilities

## Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- Git

## Setup

1. Clone this repository
2. Copy `.env.example` to `.env` and configure your environment variables:

```bash
# Odoo installation path
ODOO_PATH=/path/to/odoo

# Database name
ODOO_DB=odoo18_db

# Modules to install (comma-separated)
ODOO_MODULE_NAMES=disable_odoo_online,hr,hr_holidays,hr_expense

# Modules to disable demo data (comma-separated)
ODOO_WITHOUT_DEMO_MODULES=disable_odoo_online,hr,hr_holidays,hr_expense

# Custom addons path
CUSTOM_ADDONS_PATH=/path/to/custom-addons

# Database connection details
DB_HOST=127.0.0.1
DB_PORT=5432
DB_USER=admin
DB_PASSWORD=admin
```

## Usage

### Fresh Installation

To perform a fresh installation of Odoo modules without demo data:

```bash
./fresh_install.sh
```

This script will:
1. Clean up any existing Odoo processes to prevent database locks
2. Drop the existing database if it exists
3. Create a new database
4. Install specified modules without demo data
5. Configure the installation using environment variables
6. Generate detailed logs for debugging and monitoring

Two log files are generated during the installation:
- `fresh_install.log`: Contains step-by-step installation progress, configuration details, and module dependencies
- `odoo.log`: Contains detailed Odoo server logs including module loading, database operations, and any errors

> **Note**: The script automatically handles cleanup of existing Odoo processes to prevent database locks. This ensures a clean installation even if there are lingering processes from previous runs.

### Environment Variables

- `ODOO_PATH`: Path to your Odoo installation
- `ODOO_DB`: Name of the database to create/use
- `ODOO_MODULE_NAMES`: Comma-separated list of modules to install
- `ODOO_WITHOUT_DEMO_MODULES`: Comma-separated list of modules to install without demo data (defaults to `ODOO_MODULE_NAMES` if not set)
- `CUSTOM_ADDONS_PATH`: Path to your custom addons directory (optional)
- `DB_HOST`: Database host
- `DB_PORT`: Database port
- `DB_USER`: Database user
- `DB_PASSWORD`: Database password

## Logging

The installation process generates comprehensive logs to help with debugging and monitoring:

### Installation Logs
- `fresh_install.log`: Contains detailed information about the installation process
  - Environment setup and validation
  - Database operations
  - Module dependencies and their locations
  - Configuration file contents
  - Installation progress and status
  - Error messages (if any)

### Odoo Server Logs
- `odoo.log`: Contains detailed Odoo server logs
  - Module loading and initialization
  - Database operations
  - Server status messages
  - Detailed error traces (if any)
  - Performance metrics

Both log files are automatically created and managed by the installation script. They are useful for:
- Debugging installation issues
- Verifying module dependencies
- Monitoring installation progress
- Troubleshooting database operations

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
