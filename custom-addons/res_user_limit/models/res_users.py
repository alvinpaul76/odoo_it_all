# -*- coding: utf-8 -*-
import logging
import odoo
from odoo import models, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model_create_multi
    def create(self, vals_list):
        _logger.info('Attempting to create %d new user record(s)', len(vals_list))
        
        # Skip the check for admin/system users
        if self.env.su:
            _logger.info('Superuser mode detected, bypassing user limit check')
            return super().create(vals_list)
            
        # Get the current user count (excluding portal and public users)
        user_count = self.search_count([('share', '=', False)])
        _logger.debug('Current internal user count: %d', user_count)
        
        # Get the maximum allowed users using sudo to bypass access rights
        limit_config = self.env['res.user.limit.config'].sudo().get_user_limit()
        _logger.debug('User limit configuration: %d', limit_config)
        
        # If limit is -1, it means no limit is set
        if limit_config == -1:
            _logger.info('No user limit configured, proceeding with creation')
            return super().create(vals_list)
        
        # Count only internal users being created (not portal/public)
        internal_users_to_create = sum(1 for vals in vals_list if not vals.get('share', False))
        _logger.info('Creating %d internal users', internal_users_to_create)
        
        # Check if creating these users would exceed the limit
        if user_count + internal_users_to_create > limit_config:
            _logger.warning(
                'User creation blocked: Would exceed limit (limit: %d, current: %d, attempting to add: %d)',
                limit_config, user_count, internal_users_to_create
            )
            raise ValidationError(_(
                'Cannot create new user(s). The maximum limit of %s internal users has been reached. '
                'Current internal user count: %s'
            ) % (limit_config, user_count))
        
        _logger.info('User limit check passed, proceeding with creation')
        result = super().create(vals_list)
        _logger.info('Successfully created %d new user record(s)', len(result))
        return result
