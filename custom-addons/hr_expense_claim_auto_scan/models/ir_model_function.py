# -*- coding: utf-8 -*-
"""
This module adds a temporary ir.model.function model to the registry
to allow proper uninstallation of modules that reference this model.
"""
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class IrModelFunction(models.Model):
    """
    Temporary model to handle ir.model.function references during uninstallation.
    This model mimics the structure of the ir.model.function that would be created
    by PostgreSQL functions, allowing Odoo to properly uninstall modules that
    reference this model.
    """
    _name = 'ir.model.function'
    _description = 'Temporary Model for PostgreSQL Functions'

    name = fields.Char('Function Name', required=True)
    model_id = fields.Many2one('ir.model', string='Model', required=True, ondelete='cascade')
    module_id = fields.Many2one('ir.module.module', string='Module', required=True, ondelete='cascade')
    
    @api.model
    def _register_hook(self):
        """
        Register hook to ensure this model is loaded before uninstallation.
        """
        _logger.info("Registering ir.model.function model to handle uninstallation")
        return super(IrModelFunction, self)._register_hook()
    
    def unlink(self):
        """
        Override unlink to handle special cases during uninstallation.
        """
        _logger.info("Unlinking ir.model.function records: %s", self.ids)
        
        # Get the function names before deletion
        function_names = self.mapped('name')
        
        # Drop the PostgreSQL functions if they exist
        for function_name in function_names:
            try:
                # Try to drop the function with any number of arguments
                self.env.cr.execute(f"DROP FUNCTION IF EXISTS {function_name}")
                _logger.info("Dropped PostgreSQL function: %s", function_name)
            except Exception as e:
                _logger.warning("Failed to drop function %s: %s", function_name, e)
        
        return super(IrModelFunction, self).unlink()
