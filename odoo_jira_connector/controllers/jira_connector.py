# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
import hashlib
import hmac
import json
import logging

from odoo import http
from odoo.exceptions import ConcurrencyError
from odoo.http import request
from odoo.service.model import PG_CONCURRENCY_EXCEPTIONS_TO_RETRY

_logger = logging.getLogger(__name__)


def valid_signature(secret, body, header):
    """Check the ``X-Hub-Signature: sha256=<hex>`` header that Jira adds to
    webhooks registered with a secret (HMAC-SHA256 of the raw body)."""
    method, _sep, signature = (header or '').partition('=')
    if method.strip().lower() != 'sha256' or not signature:
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature.strip().lower())


class JiraWebhook(http.Controller):
    """Receives the webhook events sent by Jira."""

    @http.route('/jira_webhook', type='http', auth='public',
                methods=['POST'], csrf=False)
    def import_jira_data(self, **kwargs):
        """Apply a Jira webhook event when Automatic mode is enabled."""
        params = request.env['ir.config_parameter'].sudo()
        raw_data = request.httprequest.data or b''
        secret = params.get_param('odoo_jira_connector.webhook_secret')
        if not secret:
            _logger.warning("Rejected a Jira webhook call because no webhook secret is configured.")
            return request.make_json_response({'status': 'unauthorized'}, status=401)
        if not valid_signature(
                secret, raw_data, request.httprequest.headers.get('X-Hub-Signature')):
            _logger.warning("Rejected a Jira webhook call without a valid signature.")
            return request.make_json_response({'status': 'invalid signature'}, status=401)
        if not (raw_data and params.get_param('odoo_jira_connector.automatic')):
            return request.make_json_response({'status': 'received'})
        try:
            jira_data = json.loads(raw_data)
        except ValueError:
            _logger.warning("Ignored a Jira webhook call with an invalid JSON body.")
            return request.make_json_response({'status': 'invalid body'}, status=400)
        webhook_event = jira_data.get('webhookEvent') if isinstance(jira_data, dict) else None
        if webhook_event:
            try:
                with request.env.cr.savepoint():
                    request.env['project.task'].sudo().webhook_data_handle(
                        jira_data, webhook_event)
            except (*PG_CONCURRENCY_EXCEPTIONS_TO_RETRY, ConcurrencyError):
                # Let Odoo retry the request, e.g. while an export holds the lock.
                raise
            except Exception:
                _logger.exception("Failed to process Jira webhook event %s",
                                  webhook_event)
        return request.make_json_response({'status': 'received'})
