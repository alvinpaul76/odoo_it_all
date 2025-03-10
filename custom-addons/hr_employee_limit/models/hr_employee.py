import logging
from odoo import models, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.model_create_multi
    def create(self, vals_list):
        _logger.info('Attempting to create %d new employee record(s)', len(vals_list))
        
        try:
            # Get the current employee count
            employee_count = self.search_count([])
            _logger.debug('Current employee count: %d', employee_count)
            
            # Get the maximum allowed employees using sudo to bypass access rights
            limit_config = self.env['hr.employee.limit.config'].sudo().get_employee_limit()
            _logger.debug('Employee limit configuration: %d', limit_config)
            
            # Check if creating these employees would exceed the limit
            if employee_count + len(vals_list) > limit_config:
                _logger.warning(
                    'Employee creation blocked: Would exceed limit (limit: %d, current: %d, attempting to add: %d)',
                    limit_config, employee_count, len(vals_list)
                )
                raise ValidationError(_(
                    'Cannot create new employee(s). The maximum limit of %s employees has been reached. '
                    'Current employee count: %s'
                ) % (limit_config, employee_count))
            
            _logger.info('Employee limit check passed, proceeding with creation')
            result = super().create(vals_list)
            _logger.info('Successfully created %d new employee record(s)', len(vals_list))
            return result
            
        except Exception as e:
            _logger.error('Error during employee creation: %s', str(e))
            raise
