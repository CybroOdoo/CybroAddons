# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Dhanya B (odoo@cybrosys.com)
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
##############################################################################
import json
from odoo import http
from odoo.http import request


class JiraWebhook(http.Controller):
    """Class to fetch Jira data using webhook"""

    @http.route('/jira_webhook', type="json", auth='public',
                methods=['POST'], csrf=False)
    def import_jira_data(self, *args, **kwargs):
        """function to import data from Jira based on webhook events"""
        automated_import_export = request.env['ir.config_parameter'] \
            .sudo().get_param('odoo_jira_connector.automatic')
        if automated_import_export:
            data = json.loads(request.httprequest.data)
            jira = json.dumps(data, sort_keys=True,
                              indent=4, separators=(',', ': '))
            jira_data = json.loads(jira)
            webhook_event = jira_data['webhookEvent']
            delay = request.env['project.task'].sudo(). \
                with_delay(priority=1, eta=60)
            delay.webhook_data_handle(jira_data, webhook_event)
