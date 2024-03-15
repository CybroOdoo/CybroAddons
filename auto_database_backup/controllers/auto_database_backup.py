import json
from odoo import http
from odoo.http import request


class OnedriveAuth(http.Controller):
    """Controller for handling authentication with OneDrive and Google Drive."""
    @http.route('/onedrive/authentication', type='http', auth="public")
    def oauth2callback(self, **kw):
        """
             Callback function for OneDrive authentication.

                :param kw: A dictionary of keyword arguments.
                :return: A redirect response.
        """
        state = json.loads(kw['state'])
        backup_config = request.env['db.backup.configure'].sudo().browse(
            state.get('backup_config_id'))
        backup_config.get_onedrive_tokens(kw.get('code'))
        backup_config.hide_active = True
        backup_config.active = True
        return http.local_redirect(state.get('url_return'))

    @http.route('/google_drive/authentication', type='http', auth="public")
    def gdrive_oauth2callback(self, **kw):
        """Callback function for Google Drive authentication."""
        state = json.loads(kw['state'])
        backup_config = request.env['db.backup.configure'].sudo().browse(
            state.get('backup_config_id'))
        backup_config.get_gdrive_tokens(kw.get('code'))
        backup_config.hide_active = True
        backup_config.active = True
        return http.local_redirect(state.get('url_return'))
