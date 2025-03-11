# -*- coding: utf-8 -*-
import logging
# Fix import statements to avoid lint warnings
import odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)

class ResUserLimitConfig(models.Model):
    _name = 'res.user.limit.config'
    _description = 'User Limit Configuration'
    _rec_name = 'name'

    name = fields.Char(
        string='Name',
        required=True,
        help='A unique name to identify this configuration'
    )
    max_users = fields.Integer(
        string='Maximum Users',
        required=True,
        default=10,
        help='Maximum number of users allowed in the system'
    )
    # Override the standard active field to prevent automatic archiving
    active = fields.Boolean(
        string='Active', 
        default=False,  # Default to inactive
        copy=False,  # Don't copy active state when duplicating
        help='Only one configuration can be active at a time. When you activate a configuration, any previously active ones will be automatically deactivated.'
    )
    
    # Override the standard selection labels for archive/unarchive
    def _get_archive_action_label(self):
        """Change the archive button label to 'Inactive' instead of 'Archive'"""
        return _('Inactive')
    
    def _get_unarchive_action_label(self):
        """Change the unarchive button label to 'Active' instead of 'Unarchive'"""
        return _('Active')

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

    @api.constrains('max_users')
    def _check_max_users(self):
        """Validate the max_users value"""
        for record in self:
            if record.max_users <= 0:
                _logger.error(
                    'Invalid max_users value: %d. Must be greater than 0.',
                    record.max_users
                )
                raise ValidationError(_(
                    'Maximum number of users must be greater than 0'
                ))
            
            if record.max_users > 100000:
                _logger.error(
                    'Invalid max_users value: %d. Must not exceed 100,000.',
                    record.max_users
                )
                raise ValidationError(_(
                    'Maximum number of users cannot exceed 100,000'
                ))

    @api.constrains('active')
    def _check_active_configs(self):
        """Ensure only one configuration is active at a time"""
        # Skip this constraint during installation or when explicitly bypassed
        if self.env.context.get('install_mode') or self.env.context.get('bypass_active_constraint'):
            _logger.info('Bypassing constraint check during installation or with bypass context')
            return
            
        for record in self:
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
                        "UPDATE res_user_limit_config SET active = FALSE WHERE id IN %s",
                        (tuple(active_configs.ids),)
                    )
                    _logger.info('Successfully deactivated other configurations via SQL')

    @api.model
    def get_user_limit(self):
        """Get the current user limit configuration
        
        Returns:
            int: The maximum number of users allowed, or -1 if no limit is set
                (when no configuration is active)
        """
        try:
            _logger.info('Fetching current user limit configuration')
            config = self.search([('active', '=', True)], limit=1)
            
            if not config:
                _logger.info('No active configuration found - user creation will be unlimited')
                return -1  # Return -1 to indicate no limit
            
            _logger.debug(
                'Found active configuration: %s with max_users: %d',
                config.name, config.max_users
            )
            
            return config.max_users
            
        except (ValidationError, UserError) as e:
            # Catch specific exceptions instead of generic Exception
            _logger.error('Error while fetching user limit: %s', str(e))
            # In case of error, allow unlimited users rather than blocking
            _logger.warning('Due to error, defaulting to unlimited users')
            return -1

    def write(self, vals):
        """Override write method to add logging and enforce constraints"""
        if 'name' in vals:
            _logger.info(
                'Updating configuration name from "%s" to "%s"',
                self.name, vals['name']
            )
        if 'max_users' in vals:
            _logger.info(
                'Updating max_users from %d to %d for configuration: %s',
                self.max_users, vals['max_users'], self.name
            )
        
        # If explicitly setting active=True, deactivate other configurations
        if vals.get('active'):
            _logger.info('Activating configuration: %s', self.name)
            if not self.env.context.get('install_mode') and not self.env.context.get('bypass_active_constraint'):
                self.env.cr.execute(
                    "UPDATE res_user_limit_config SET active = FALSE WHERE id != %s AND active = TRUE",
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
                
            # Set default active value to False if not specified
            if 'active' not in vals:
                vals['active'] = False
                _logger.info('Creating new inactive configuration by default')
            
            # If trying to create an active configuration, disable any existing active ones
            # Skip this check during installation or when explicitly bypassed
            if vals.get('active') and not self.env.context.get('install_mode') and not self.env.context.get('bypass_active_constraint'):
                # Use direct SQL to disable all active configurations
                self.env.cr.execute(
                    "UPDATE res_user_limit_config SET active = FALSE WHERE active = TRUE"
                )
                _logger.info('Deactivated all existing active configurations via SQL before creating new one')
            
            _logger.info('Creating new user limit configuration with values: %s', vals)
        
        return super().create(vals_list)
    
    def toggle_active(self):
        """Override toggle_active to handle activation/deactivation"""
        # This method is called by the standard Odoo UI when clicking the archive/unarchive button
        
        for record in self:
            # We're toggling active status
            if not record.active:
                # If we're activating this record, automatically deactivate any other active records
                other_active_configs = self.with_context(active_test=False).search([('active', '=', True)])
                if other_active_configs:
                    _logger.info('Deactivating other active configurations: %s', other_active_configs.mapped('name'))
                    # Use direct SQL to ensure this always works
                    self.env.cr.execute(
                        "UPDATE res_user_limit_config SET active = FALSE WHERE id IN %s",
                        (tuple(other_active_configs.ids),)
                    )
                
                _logger.info('Activating configuration: %s (ID: %s)', record.name, record.id)
                # Use direct SQL to ensure this always works
                self.env.cr.execute(
                    "UPDATE res_user_limit_config SET active = TRUE WHERE id = %s",
                    (record.id,)
                )
            else:
                # Deactivating the configuration
                _logger.info('Deactivating configuration: %s (ID: %s)', record.name, record.id)
                # Use direct SQL to ensure this always works
                self.env.cr.execute(
                    "UPDATE res_user_limit_config SET active = FALSE WHERE id = %s",
                    (record.id,)
                )
        
        # Return False to prevent the standard toggle_active behavior
        return False
    
    def copy(self, default=None):
        """When duplicating a configuration, ensure it's created as inactive"""
        default = dict(default or {})
        default.update({
            'name': _('%s (Copy)') % self.name,
            'active': False,  # Not active by default
        })
        return super().copy(default)
    
    @api.model
    def get_active_config(self):
        """Get the complete active configuration record"""
        try:
            # Include all records in the search regardless of visibility
            config = self.with_context(active_test=False).search([('active', '=', True)], limit=1)
            if not config:
                _logger.warning('No active configuration found')
                raise UserError(_(
                    'No active user limit configuration found. '
                    'Please activate one of the existing configurations or create a new one.'
                ))
            _logger.info('Returning active configuration: %s (ID: %s)', config.name, config.id)
            return config
        except (ValidationError, UserError) as e:
            # Catch specific exceptions instead of generic Exception
            _logger.error('Error while fetching active configuration: %s', str(e))
            raise UserError(_(
                'Error while fetching active user limit configuration. '
                'Please contact your system administrator.'
            ))
            
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
        except (ValidationError, UserError, odoo.exceptions.AccessError) as e:
            # Catch specific exceptions instead of generic Exception
            _logger.error('Error while activating default configuration: %s', str(e))
            return False
