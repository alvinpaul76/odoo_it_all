# -*- coding: utf-8 -*-

import logging
import werkzeug.utils
from urllib.parse import urlencode
from odoo import http, models, api
from odoo.http import request
from odoo.tools import config

_logger = logging.getLogger(__name__)

# Log that the module is being loaded
_logger.info("Disable Debug Mode module is being loaded")

class IrHttpInherit(models.AbstractModel):
    _inherit = 'ir.http'
    
    @classmethod
    def _dispatch(cls, endpoint):
        """
        Override the _dispatch method to check for debug mode access
        """
        # Check if debug mode is being requested
        debug_requested = False
        if request and request.httprequest and request.httprequest.args:
            debug_param = request.httprequest.args.get('debug')
            if debug_param:
                debug_requested = True
                _logger.info("Debug mode requested via URL parameter: %s", debug_param)
        
        # If debug mode is requested, check if user is admin
        if debug_requested and request.session and hasattr(request.session, 'uid') and request.session.uid:
            try:
                # Get the user from the environment
                user = request.env['res.users'].sudo().browse(request.session.uid)
                is_admin = user.has_group('base.group_system')
                
                _logger.info(
                    "Debug access check - User: %s (ID: %s), Is Admin: %s",
                    user.name, user.id, is_admin
                )
                
                # If not admin, redirect without debug parameter
                if not is_admin:
                    _logger.info(
                        'Non-admin user %s (ID: %s) attempted to access debug mode - redirecting',
                        user.name, user.id
                    )
                    
                    # Clear debug from session
                    if hasattr(request.session, 'debug'):
                        request.session.debug = ''
                    
                    # Get current URL and query parameters
                    path_info = request.httprequest.path
                    query_params = dict(request.httprequest.args.items())
                    
                    # Remove debug parameter
                    if 'debug' in query_params:
                        del query_params['debug']
                    
                    # Build new URL without debug parameter
                    new_query_string = urlencode(query_params)
                    redirect_url = path_info
                    if new_query_string:
                        redirect_url += '?' + new_query_string
                    
                    _logger.info("Redirecting to: %s", redirect_url)
                    
                    # Redirect to the same page without debug
                    return werkzeug.utils.redirect(redirect_url)
            except Exception as e:
                _logger.error("Error in debug mode restriction: %s", str(e), exc_info=True)
        
        # Continue with normal dispatch
        return super(IrHttpInherit, cls)._dispatch(endpoint)

# Controller to handle debug mode access
class DisableDebugModeController(http.Controller):
    
    @http.route('/web/session/get_session_info', type='json', auth="user")
    def get_session_info(self):
        """
        Override the session info method to check debug access
        """
        # Get the original session info
        result = request.env['ir.http'].session_info()
        
        # Check if the user is an admin
        user = request.env.user
        is_admin = user.has_group('base.group_system')
        
        # If not admin, ensure debug is disabled
        if not is_admin and result.get('debug', False):
            _logger.info(
                'Non-admin user %s (ID: %s) attempted to access debug mode - blocking in session info',
                user.name, user.id
            )
            result['debug'] = False
        
        return result
