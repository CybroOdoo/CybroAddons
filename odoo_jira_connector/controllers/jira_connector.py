# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import json
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class JiraWebhook(http.Controller):
    """Class to fetch Jira data using webhook"""

    @http.route('/jira_webhook', type="http", auth='public',
                methods=['POST'], csrf=False)
    def import_jira_data(self, **kwargs):
        """function to import data from Jira based on webhook events"""
        automated_import_export = request.env['ir.config_parameter'].sudo().get_param('odoo_jira_connector.automatic')
        if automated_import_export:
            try:
                raw_data = request.httprequest.data
                if raw_data:
                    jira_data = json.loads(raw_data)
                    webhook_event = jira_data.get('webhookEvent')
                    if webhook_event:
                        request.env['project.task'].sudo().webhook_data_handle(jira_data, webhook_event)
            except Exception as e:
                _logger.error("Failed to process Jira webhook: %s", e)
        return request.make_json_response({"status": "received"})
