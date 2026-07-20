# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import json
import logging
from datetime import datetime

from werkzeug.exceptions import Forbidden, NotFound

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class OnedriveAuth(http.Controller):
    """Handle OneDrive and Google Drive OAuth authentication callbacks."""

    @staticmethod
    def _safe_redirect_url(url_return, base_url):
        """Return ``url_return`` only when it points to this Odoo instance,
        otherwise fall back to the web client. This prevents the callback
        from being abused as an open redirect."""
        if url_return and base_url and url_return.startswith(base_url):
            return url_return
        return '/web'

    def _handle_oauth_callback(self, provider, token_method, **kw):
        """Shared, validated handling for the OAuth callbacks.

        :param provider: human readable provider name (for logging)
        :param token_method: name of the ``db.backup.configure`` method that
            exchanges the authorization code for tokens
        """
        state_raw = kw.get('state')
        code = kw.get('code')
        if not state_raw or not code:
            _logger.warning("%s OAuth callback missing state or code",
                            provider)
            return request.redirect('/web')
        try:
            state = json.loads(state_raw)
        except (ValueError, TypeError):
            _logger.warning("%s OAuth callback with invalid state", provider)
            return request.redirect('/web')
        backup_config = request.env['db.backup.configure'].sudo().browse(
            state.get('backup_config_id')).exists()
        if not backup_config:
            _logger.warning("%s OAuth callback for unknown configuration %s",
                            provider, state.get('backup_config_id'))
            return request.redirect('/web')
        getattr(backup_config, token_method)(code)
        backup_config.hide_active = True
        backup_config.active = True
        base_url = request.env['ir.config_parameter'].sudo().get_param(
            'web.base.url')
        return request.redirect(
            self._safe_redirect_url(state.get('url_return'), base_url))

    @http.route('/onedrive/authentication', type='http', auth="public")
    def oauth2callback(self, **kw):
        """Callback function for OneDrive authentication."""
        return self._handle_oauth_callback(
            'OneDrive', 'get_onedrive_tokens', **kw)

    @http.route('/google_drive/authentication', type='http', auth="public")
    def gdrive_oauth2callback(self, **kw):
        """Callback function for Google Drive authentication."""
        return self._handle_oauth_callback(
            'Google Drive', 'get_gdrive_tokens', **kw)


class DbBackupDownload(http.Controller):
    """Download a freshly generated database backup from the browser."""

    @http.route('/auto_database_backup/download/<int:config_id>',
                type='http', auth='user')
    def download_backup(self, config_id, **kw):
        """Generate a fresh backup for the given configuration and return it
        as a file download. Restricted to backup managers; the dump runs as
        the scheduled-action user to satisfy the cron-only guard."""
        env = request.env
        if not env.user.has_group(
                'auto_database_backup.group_auto_database_backup_manager'):
            raise Forbidden()
        config = env['db.backup.configure'].sudo().browse(config_id).exists()
        if not config:
            raise NotFound()
        target_db = config.db_name or next(
            iter(config._get_target_databases()), None)
        if not target_db:
            raise NotFound()
        cron = env.ref('auto_database_backup.ir_cron_auto_db_backup_'
                       '%s' % config.backup_frequency)
        try:
            result = config.with_user(cron.user_id.id).dump_data(
                target_db, None, config.backup_format,
                config.backup_frequency)
        except Exception as error:
            _logger.exception("Backup download failed for configuration %s",
                              config_id)
            return request.make_response(
                "Backup download failed: %s" % error,
                headers=[('Content-Type', 'text/plain')], status=500)
        if hasattr(result, 'read'):
            result.seek(0)
            data = result.read()
        else:
            data = result
        backup_time = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{target_db}_{backup_time}.{config.backup_format}"
        return request.make_response(data, headers=[
            ('Content-Type', 'application/octet-stream'),
            ('Content-Disposition', http.content_disposition(filename)),
            ('Content-Length', len(data)),
        ])
