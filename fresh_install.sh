#!/bin/bash

# Exit on error
set -e

# Store original directory
ORIGINAL_DIR=$(pwd)

# Set up logging with absolute paths
LOG_FILE="$ORIGINAL_DIR/fresh_install.log"
ODOO_LOG_FILE="$ORIGINAL_DIR/odoo.log"

log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $1" | tee -a "$LOG_FILE"
}

# Clear previous logs
> "$LOG_FILE"
> "$ODOO_LOG_FILE"

# Ensure Odoo log directory exists and is writable
touch "$ODOO_LOG_FILE"
chmod 666 "$ODOO_LOG_FILE"

log "Starting fresh installation script..."

# Load environment variables
if [ -f ".env" ]; then
    source .env
    log "Loaded environment variables from .env file"
else
    log "Error: .env file not found"
    exit 1
fi

# Check if ODOO_PATH and ODOO_MODULE_NAMES are set
if [ -z "$ODOO_PATH" ] || [ -z "$ODOO_MODULE_NAMES" ]; then
    log "Error: ODOO_PATH and ODOO_MODULE_NAMES must be set in .env file"
    exit 1
fi

# Check if ODOO_DB is set
if [ -z "$ODOO_DB" ]; then
    log "Error: ODOO_DB must be set in .env file"
    exit 1
fi

# Log directory change
log "Changing directory to: $ODOO_PATH"

# Navigate to Odoo directory
cd "$ODOO_PATH"
log "Current directory: $(pwd)"

# Activate virtual environment
log "Activating virtual environment..."
source venv/bin/activate
log "Python version: $(python3 --version)"

# Check if database connection details are set
if [ -z "$DB_HOST" ] || [ -z "$DB_PORT" ] || [ -z "$DB_USER" ] || [ -z "$DB_PASSWORD" ]; then
    log "Error: Database connection details must be set in .env file"
    exit 1
fi

# Set default addons paths
DEFAULT_ADDONS_PATH="$ODOO_PATH/addons,$ODOO_PATH/odoo/addons"

# Use custom addons path if provided, otherwise use default
ADDONS_PATH=${CUSTOM_ADDONS_PATH:+"$DEFAULT_ADDONS_PATH,$CUSTOM_ADDONS_PATH"}
ADDONS_PATH=${ADDONS_PATH:-"$DEFAULT_ADDONS_PATH"}

# Install modules without demo data
log "Installing modules: $ODOO_MODULE_NAMES without demo data..."
log "Using addons path: $ADDONS_PATH"
log "Modules with demo data disabled: $ODOO_WITHOUT_DEMO_MODULES"
# Kill any existing Odoo processes
log "Cleaning up existing Odoo processes..."
pkill -f "odoo-bin" || true

# Wait a moment for processes to terminate
log "Waiting for processes to terminate..."
sleep 2

# Drop database if it exists
log "Dropping database if it exists..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" postgres -c "DROP DATABASE IF EXISTS \"$ODOO_DB\"" 2>&1 | while IFS= read -r line; do
    log "DB: $line"
done

# Check if ODOO_WITHOUT_DEMO_MODULES is set
if [ -z "$ODOO_WITHOUT_DEMO_MODULES" ]; then
    # Default to the same modules as ODOO_MODULE_NAMES if not set
    ODOO_WITHOUT_DEMO_MODULES="$ODOO_MODULE_NAMES"
fi

# Create configuration file
log "Creating Odoo configuration file..."
cat > odoo.conf << EOL
[options]
without_demo = all
no_database_list = True
demo = {}
load_language = en_US
server_wide_modules = base
log_db = False
log_db_level = debug
log_handler = :DEBUG
log_level = debug
logfile = "$ODOO_LOG_FILE"

# Disable demo data for specific modules
[options.without_demo]
all = True
base = True
EOL

# Add without_demo options for each module
for module in $(echo "$ODOO_WITHOUT_DEMO_MODULES" | tr ',' ' '); do
    if [ ! -z "$module" ]; then
        echo "$module = True" >> odoo.conf
    fi
done

# Add demo section
cat >> odoo.conf << EOL

# Prevent auto-installation of demo data
[options.demo]
all = False
base = False
EOL

# Add demo = False for each module
for module in $(echo "$ODOO_WITHOUT_DEMO_MODULES" | tr ',' ' '); do
    if [ ! -z "$module" ]; then
        echo "$module = False" >> odoo.conf
    fi
done

# Set environment variables to prevent demo data
log "Setting up environment variables..."

# Log configuration file contents for debugging
log "Configuration file contents:"
log "$(cat odoo.conf)"

# Log module dependencies
log "Checking module dependencies..."
for module in $(echo "$ODOO_MODULE_NAMES" | tr ',' ' '); do
    manifest_file="$(find "$ODOO_PATH" -name "__manifest__.py" -path "*/$module/*")"
    if [ -f "$manifest_file" ]; then
        log "Found manifest for module: $module"
        log "Manifest location: $manifest_file"
        log "Module dependencies:"
        grep -A 10 "depends" "$manifest_file" | tee -a "$LOG_FILE"
    else
        log "Warning: Could not find manifest for module: $module"
    fi
done

# Set up logging level for Odoo
export PYTHONPATH="$ODOO_PATH"
export LOG_LEVEL=${LOG_LEVEL:-debug}

log "Starting Odoo installation..."
log "Log level: $LOG_LEVEL"
log "Command: odoo-bin -d $ODOO_DB -i $ODOO_MODULE_NAMES"

# Install modules without demo data

# Execute Odoo command and capture all output
# Run Odoo with logging to both console and file
# Run Odoo installation
log "Starting Odoo installation with absolute paths..."
log "Using config file: $(pwd)/odoo.conf"

# Ensure log files are writable
touch "$LOG_FILE" "$ODOO_LOG_FILE"
chmod 666 "$LOG_FILE" "$ODOO_LOG_FILE"

{
    PYTHONPATH="$ODOO_PATH" python3 ./odoo-bin \
        -d "$ODOO_DB" \
        -i "$ODOO_MODULE_NAMES" \
        --db_host="$DB_HOST" \
        --db_port="$DB_PORT" \
        --db_user="$DB_USER" \
        --db_password="$DB_PASSWORD" \
        --http-port=8071 \
        --addons-path="$ADDONS_PATH" \
        --without-demo=all \
        --stop-after-init \
        --no-database-list \
        --load-language=en_US \
        --config=odoo.conf \
        --without-demo="$ODOO_WITHOUT_DEMO_MODULES" \
        --log-level=debug \
        --log-handler=:DEBUG \
        --log-handler=odoo:DEBUG \
        --log-handler=odoo.modules.loading:DEBUG \
        --log-handler=odoo.addons:DEBUG \
        --logfile="$ODOO_LOG_FILE"
} 2>&1 | while IFS= read -r line; do
    log "ODOO: $line"
done

# Check if installation was successful
if [ $? -eq 0 ]; then
    log "Odoo installation completed successfully"
else
    log "Error: Odoo installation failed"
    exit 1
fi

log "Installation complete!"
log "----------------------------------------"
log "Log files available:"
log "- Script log: $LOG_FILE"
log "- Odoo log: $ODOO_LOG_FILE"
log "----------------------------------------"

# Show last few lines of Odoo log
log "Last few lines of Odoo log:"
if [ -f "$ODOO_LOG_FILE" ] && [ -s "$ODOO_LOG_FILE" ]; then
    log "----------------------------------------"
    tail -n 10 "$ODOO_LOG_FILE" | while read -r line; do
        log "  $line"
    done
    log "----------------------------------------"
    log "Full logs available in: $ODOO_LOG_FILE"
else
    log "  Warning: Odoo log file is empty or not found at: $ODOO_LOG_FILE"
fi
