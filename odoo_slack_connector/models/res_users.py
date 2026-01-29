# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


from odoo import fields, models
import requests, json


class ResPartner(models.Model):
    _inherit = 'res.users'
    _description = 'Slack users'

    slack_user_id = fields.Char(string="Slack User ID")
    is_slack_internal_users = fields.Boolean("Slack User", default=False)

    def sync_users(self):
        """To load slack users"""
        slack_internal_user_list = []

        url1 = "https://slack.com/api/users.list"
        company_record = self.env.user.company_id
        payload = {}
        headers = {
            'Authorization': 'Bearer ' + company_record.token
        }

        users_response = requests.request("GET", url1, headers=headers,
                                          data=payload)
        users_response = users_response.__dict__['_content']
        dict_users = users_response.decode("UTF-8")
        users = json.loads(dict_users)
        for user_id in self:
            slack_internal_user_list.append(user_id.slack_user_id)
        # print('user_id==', slack_internal_user_list)

        for rec in users['members']:
            if rec['is_email_confirmed'] is True:
                if 'email' in rec['profile']:
                    email = rec['profile']['email']
                else:
                    email = ''
                if rec['id'] not in slack_internal_user_list:
                    vals = {
                        'name': rec['real_name'],
                        'slack_user_id': rec['id'],
                        'is_slack_internal_users': True,
                        'login': email,
                    }
                    self.create(vals)
