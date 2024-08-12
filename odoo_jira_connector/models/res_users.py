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
import re
import requests
from odoo import api, fields, models


class ResUsers(models.Model):
    """
    This class is inherited for adding an extra field and
    override the create function.
     Methods:
        create():
            extends create(vals_list) for exporting the new users to Jira
    """
    _inherit = 'res.users'

    jira_user_key = fields.Char(string='Jira User Key',
                                help='The user key of Jira.', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        """ Overrides the create method of users for exporting the new users
        to Jira """
        ir_config_parameter = self.env['ir.config_parameter'].sudo()
        jira_connection = ir_config_parameter.get_param(
            'odoo_jira_connector.connection')
        if jira_connection:
            user_auth = ir_config_parameter.get_param(
                'odoo_jira_connector.user_id_jira')
            password = ir_config_parameter.get_param(
                'odoo_jira_connector.api_token')
            users = super(ResUsers, self).create(vals_list)
            odoo_user_url = ir_config_parameter.get_param(
                'odoo_jira_connector.url') + 'rest/api/3/user'
            odoo_user_headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            payload = json.dumps({
                'emailAddress': users.login,
                'displayName': users.name,
                'name': users.name,
                'products':[]
            })
            match = re.search('^\S+@\S+\.\S+$', users.login)
            if match and match.string == str(users.login):
                response = requests.post(
                    odoo_user_url, headers=odoo_user_headers, data=payload,
                    auth=(user_auth, password))
                data = response.json()
                users.write({'jira_user_key': data['accountId']})
            return users
        else:
            users = super(ResUsers, self).create(vals_list)
            for user in users:
                # if partner is global we keep it that way
                if user.partner_id.company_id:
                    user.partner_id.company_id = user.company_id
                user.partner_id.active = user.active
            return users
