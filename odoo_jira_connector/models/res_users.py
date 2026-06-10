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
import re
import requests
from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    jira_user_key = fields.Char(string='Jira User Key', help='The user key of Jira.')

    @api.model_create_multi
    def create(self, vals_list):
        """ Overrides the create method of users for exporting the new users
        to Jira """
        users = super(ResUsers, self).create(vals_list)
        ir_config_parameter = self.env['ir.config_parameter'].sudo()
        if ir_config_parameter.get_param('odoo_jira_connector.automatic'):
            jira_connection = ir_config_parameter.get_param('odoo_jira_connector.connection')
            if jira_connection:
                jira_url = ir_config_parameter.get_param('odoo_jira_connector.url')
                if jira_url:
                    jira_url = jira_url.rstrip('/')
                    user_auth = ir_config_parameter.get_param('odoo_jira_connector.user_id_jira')
                    password = ir_config_parameter.get_param('odoo_jira_connector.api_token')
                    
                    odoo_user_url = jira_url + '/rest/api/3/user'
                    odoo_user_headers = {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json',
                        'X-Atlassian-Token': 'no-check'
                    }
                    
                    for user in users:
                        # Skip if user already has a Jira User Key (meaning they were imported/mapped from Jira)
                        if user.jira_user_key:
                            continue
                        if user.login:
                            match = re.search('^\S+@\S+\.\S+$', user.login)
                            if match and match.string == str(user.login):
                                payload = json.dumps({
                                    'emailAddress': user.login,
                                    'displayName': user.name,
                                    'name': user.name,
                                    'products': []
                                })
                                try:
                                    response = requests.post(
                                        odoo_user_url, headers=odoo_user_headers, data=payload,
                                        auth=(user_auth, password), timeout=10)
                                    if response.ok:
                                        data = response.json()
                                        if isinstance(data, dict) and 'accountId' in data:
                                            user.write({'jira_user_key': data['accountId']})
                                except Exception:
                                    continue
        return users
