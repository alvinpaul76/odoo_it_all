import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)

class HrEmployeeLimitConfig(models.Model):
    _name = 'hr.employee.limit.config'
    _description = 'Employee Limit Configuration'
    _inherit = ['mail.thread']
    # We'll display all records by default, regardless of active status
    _rec_name = 'name'

    name = fields.Char(
        string='Name',
        required=True,
        help='A unique name to identify this configuration'
    )
    max_employees = fields.Integer(
        string='Maximum Employees',
        required=True,
        default=45,
        help='Maximum number of employees allowed in the system'
    )
    # Override the standard active field to prevent automatic archiving
    active = fields.Boolean(
        string='Active', 
        default=False,  # Default to inactive
        copy=False,  # Don't copy active state when duplicating
        tracking=True,  # Track changes to this field
        help='Only one configuration can be active at a time. When you activate a configuration, any previously active ones will be automatically deactivated.'
    )
    
    # Override the standard selection labels for archive/unarchive
    def _get_archive_action_label(self):
        """Change the archive button label to 'Inactive' instead of 'Archive'"""
        return _('Inactive')
    
    def _get_unarchive_action_label(self):
        """Change the unarchive button label to 'Active' instead of 'Unarchive'"""
        return _('Active')
    
    # Add a field to track the business logic activation state separately from the UI active state
    is_enabled = fields.Boolean(
        string='Enabled',
        default=False,
        tracking=True,
        help='Indicates if this configuration is currently in use'
    )

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Configuration name must be unique!')
    ]
    
    @api.constrains('name')
    def _check_name(self):
        """Validate the name value"""
        for record in self:
            if not record.name or len(record.name.strip()) == 0:
                _logger.error('Invalid configuration name: empty name is not allowed')
                raise ValidationError(_('Configuration name cannot be empty'))
            
            # Check for duplicates (this is also enforced by SQL constraint, but this gives a nicer error message)
            domain = [('name', '=', record.name)]
            if record.id:
                domain.append(('id', '!=', record.id))
            
            duplicate = self.search(domain, limit=1)
            if duplicate:
                _logger.error(
                    'Duplicate configuration name detected: %s (existing ID: %s, new ID: %s)',
                    record.name, duplicate.id, record.id or 'new'
                )
                raise ValidationError(_(
                    'Configuration name must be unique! A configuration with name "%s" already exists.'
                ) % record.name)

    @api.constrains('max_employees')
    def _check_max_employees(self):
        """Validate the max_employees value"""
        for record in self:
            if record.max_employees <= 0:
                _logger.error(
                    'Invalid max_employees value: %d. Must be greater than 0.',
                    record.max_employees
                )
                raise ValidationError(_(
                    'Maximum number of employees must be greater than 0'
                ))
            
            if record.max_employees > 100000:
                _logger.error(
                    'Invalid max_employees value: %d. Must not exceed 100,000.',
                    record.max_employees
                )
                raise ValidationError(_(
                    'Maximum number of employees cannot exceed 100,000'
                ))

    @api.constrains('is_enabled', 'active')
    def _check_active_configs(self):
        """Ensure only one configuration is enabled and active at a time"""
        # Skip this constraint during installation or when explicitly bypassed
        if self.env.context.get('install_mode') or self.env.context.get('bypass_active_constraint'):
            _logger.info('Bypassing constraint check during installation or with bypass context')
            return
            
        for record in self:
            # Check for is_enabled constraint
            if record.is_enabled:
                # Find other enabled configurations (including archived ones)
                enabled_configs = self.with_context(active_test=False).search([('is_enabled', '=', True), ('id', '!=', record.id)])
                if enabled_configs:
                    enabled_names = ', '.join(enabled_configs.mapped('name'))
                    _logger.warning(
                        'Multiple enabled configurations detected: %s and %s. Cannot have more than one enabled configuration.',
                        record.name, enabled_names
                    )
                    # Automatically disable other configurations instead of raising an error
                    _logger.info('Automatically disabling other configurations: %s', enabled_names)
                    # Use sudo() and direct SQL to ensure this always works
                    self.env.cr.execute(
                        "UPDATE hr_employee_limit_config SET is_enabled = FALSE WHERE id IN %s",
                        (tuple(enabled_configs.ids),)
                    )
                    _logger.info('Successfully disabled other configurations via SQL')
            
            # Check for active constraint
            if record.active:
                # Find other active configurations
                active_configs = self.with_context(active_test=False).search([('active', '=', True), ('id', '!=', record.id)])
                if active_configs:
                    active_names = ', '.join(active_configs.mapped('name'))
                    _logger.warning(
                        'Multiple active configurations detected: %s and %s. Cannot have more than one active configuration.',
                        record.name, active_names
                    )
                    # Automatically deactivate other configurations
                    _logger.info('Automatically deactivating other configurations: %s', active_names)
                    # Use direct SQL to ensure this always works
                    self.env.cr.execute(
                        "UPDATE hr_employee_limit_config SET active = FALSE WHERE id IN %s",
                        (tuple(active_configs.ids),)
                    )
                    _logger.info('Successfully deactivated other configurations via SQL')

    @api.model
    def get_employee_limit(self):
        """Get the current employee limit configuration
        
        Returns:
            int: The maximum number of employees allowed, or -1 if no limit is set
                (when no configuration is enabled)
        """
        try:
            _logger.info('Fetching current employee limit configuration')
            config = self.search([('is_enabled', '=', True)], limit=1)
            
            if not config:
                _logger.info('No enabled configuration found - employee creation will be unlimited')
                return -1  # Return -1 to indicate no limit
            
            _logger.debug(
                'Found enabled configuration: %s with max_employees: %d',
                config.name, config.max_employees
            )
            
            return config.max_employees
            
        except Exception as e:
            _logger.error('Error while fetching employee limit: %s', str(e))
            # In case of error, allow unlimited employees rather than blocking
            _logger.warning('Due to error, defaulting to unlimited employees')
            return -1

    def write(self, vals):
        """Override write method to add logging and enforce constraints"""
        if 'name' in vals:
            _logger.info(
                'Updating configuration name from "%s" to "%s"',
                self.name, vals['name']
            )
        if 'max_employees' in vals:
            _logger.info(
                'Updating max_employees from %d to %d for configuration: %s',
                self.max_employees, vals['max_employees'], self.name
            )
        if 'is_enabled' in vals:
            if vals['is_enabled']:
                _logger.info('Enabling configuration: %s', self.name)
                # If we're enabling this configuration, make sure no others are enabled
                if not self.env.context.get('install_mode') and not self.env.context.get('bypass_active_constraint'):
                    # Use direct SQL to disable other enabled configurations
                    self.env.cr.execute(
                        "UPDATE hr_employee_limit_config SET is_enabled = FALSE WHERE id != %s AND is_enabled = TRUE",
                        (self.id,)
                    )
                    _logger.info('Disabled other enabled configurations via SQL')
                    
                # When enabling a configuration, also make it active and deactivate others
                vals['active'] = True
                if not self.env.context.get('install_mode') and not self.env.context.get('bypass_active_constraint'):
                    self.env.cr.execute(
                        "UPDATE hr_employee_limit_config SET active = FALSE WHERE id != %s AND active = TRUE",
                        (self.id,)
                    )
                    _logger.info('Deactivated other active configurations via SQL')
            else:
                _logger.info('Disabling configuration: %s', self.name)
        
        # If explicitly setting active=True, deactivate other configurations
        if vals.get('active'):
            _logger.info('Activating configuration: %s', self.name)
            if not self.env.context.get('install_mode') and not self.env.context.get('bypass_active_constraint'):
                self.env.cr.execute(
                    "UPDATE hr_employee_limit_config SET active = FALSE WHERE id != %s AND active = TRUE",
                    (self.id,)
                )
                _logger.info('Deactivated other active configurations via SQL')
                
        return super().write(vals)
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create method to add logging and enforce constraints"""
        for vals in vals_list:
            # Make sure name is provided
            if not vals.get('name'):
                _logger.error('Attempt to create configuration without name')
                raise ValidationError(_('Configuration name is required'))
                
            # Set default active value to False
            vals['active'] = False
            
            # Set default is_enabled status to False if not specified
            if 'is_enabled' not in vals:
                vals['is_enabled'] = False
                _logger.info('Creating new disabled configuration by default')
            
            # If trying to create an enabled configuration, disable any existing enabled ones
            # Skip this check during installation or when explicitly bypassed
            if vals.get('is_enabled') and not self.env.context.get('install_mode') and not self.env.context.get('bypass_active_constraint'):
                # Use direct SQL to disable all enabled configurations
                self.env.cr.execute(
                    "UPDATE hr_employee_limit_config SET is_enabled = FALSE WHERE is_enabled = TRUE"
                )
                _logger.info('Disabled all existing enabled configurations via SQL before creating new one')
            
            _logger.info('Creating new employee limit configuration with values: %s', vals)
        
        return super().create(vals_list)
    
    def toggle_active(self):
        """Override toggle_active to handle both active and is_enabled states"""
        # This method is called by the standard Odoo UI when clicking the archive/unarchive button
        
        for record in self:
            # We're toggling both active and is_enabled
            if not record.active:
                # If we're activating this record, automatically deactivate any other active records
                other_active_configs = self.with_context(active_test=False).search([('active', '=', True)])
                if other_active_configs:
                    _logger.info('Deactivating other active configurations: %s', other_active_configs.mapped('name'))
                    # Use direct SQL to ensure this always works
                    self.env.cr.execute(
                        "UPDATE hr_employee_limit_config SET active = FALSE WHERE id IN %s",
                        (tuple(other_active_configs.ids),)
                    )
                
                # Also enable this configuration and disable others
                other_enabled_configs = self.with_context(active_test=False).search([('is_enabled', '=', True)])
                if other_enabled_configs:
                    _logger.info('Disabling other enabled configurations: %s', other_enabled_configs.mapped('name'))
                    # Use direct SQL to ensure this always works
                    self.env.cr.execute(
                        "UPDATE hr_employee_limit_config SET is_enabled = FALSE WHERE id IN %s",
                        (tuple(other_enabled_configs.ids),)
                    )
                
                _logger.info('Activating and enabling configuration: %s (ID: %s)', record.name, record.id)
                # Use direct SQL to ensure this always works
                self.env.cr.execute(
                    "UPDATE hr_employee_limit_config SET active = TRUE, is_enabled = TRUE WHERE id = %s",
                    (record.id,)
                )
            else:
                # Deactivating and disabling the configuration
                _logger.info('Deactivating and disabling configuration: %s (ID: %s)', record.name, record.id)
                # Use direct SQL to ensure this always works
                self.env.cr.execute(
                    "UPDATE hr_employee_limit_config SET active = FALSE, is_enabled = FALSE WHERE id = %s",
                    (record.id,)
                )
        
        # Return False to prevent the standard toggle_active behavior
        return False
    
    def copy(self, default=None):
        """When duplicating a configuration, ensure it's created as visible but disabled"""
        default = dict(default or {})
        default.update({
            'name': _('%s (Copy)') % self.name,
            'active': False,  # Not visible in the UI by default
            'is_enabled': False,  # Not enabled by default
        })
        return super().copy(default)
    
    @api.model
    def get_active_config(self):
        """Get the complete enabled configuration record"""
        try:
            # Include all records in the search regardless of visibility
            config = self.with_context(active_test=False).search([('is_enabled', '=', True)], limit=1)
            if not config:
                _logger.warning('No enabled configuration found')
                raise UserError(_(
                    'No enabled employee limit configuration found. '
                    'Please enable one of the existing configurations or create a new one.'
                ))
            _logger.info('Returning enabled configuration: %s (ID: %s)', config.name, config.id)
            return config
        except Exception as e:
            _logger.error('Error while fetching active configuration: %s', str(e))
            raise UserError(_(
                'Error while fetching active employee limit configuration. '
                'Please contact your system administrator.'
            )) from e
            
    @api.model
    def _activate_default_if_none_active(self, record_ids):
        """Activate the default configuration if no active configuration exists.
        This method is called from XML data loading to safely activate the default config.
        """
        try:
            # Check if any active configuration exists
            active_config = self.search([('active', '=', True)], limit=1)
            if not active_config and record_ids:
                # Get the record to activate
                default_config = self.browse(record_ids[0])
                if default_config.exists():
                    _logger.info('No active configuration found. Activating default: %s (ID: %s)', 
                                default_config.name, default_config.id)
                    # Directly set active=True to bypass constraints during module installation
                    default_config.with_context(install_mode=True).write({'active': True})
                    return True
            return False
        except Exception as e:
            _logger.error('Error while activating default configuration: %s', str(e))
            return False
