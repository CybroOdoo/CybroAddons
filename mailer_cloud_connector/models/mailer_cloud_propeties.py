# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
import requests
from odoo import api, fields, models


class MailerCloudList(models.Model):
    """
        Model representing properties in Mailer Cloud associated with Odoo records.
        """
    _name = 'mailer.cloud.properties'
    _description = 'List of Mail Cloud properties'

    mailer_cloud = fields.Char(string='Mailer Cloud',
                               help="Mailer Cloud property identifier.")
    name = fields.Char(
        string='Property Name', required=True,
        help="Name of the Mailer Cloud property.")
    type = fields.Selection(
        [
            ('text', 'Text'),
            ('number', 'Number'),
            ('date', 'Date'),
            ('textarea', 'Textarea')
        ],
        string='Type', required=True,
        help="Type of the Mailer Cloud property.")
    authorization_id = fields.Many2one(
        'mailer.cloud.api.sync', ondelete='cascade',
        help="Authorization associated with this property.")

    @api.model
    def create(self, vals_list):
        """
                Override the create method to synchronize property creation with Mailer Cloud.

                :param vals_list: Dictionary of values for creating the record.
                :return: Newly created record.
                """
        res = super(MailerCloudList, self).create(vals_list)
        try:
            url = "https://cloudapi.mailercloud.com/v1/contact/property"

            payload = json.dumps({
                "name": res.name,
                "type": res.type
            })
            headers = {
                'Authorization': res.authorization_id.api_key,
                'Content-Type': 'application/json'
            }
            response = requests.request("POST", url, headers=headers,
                                        data=payload)
            res.write({
                'mailer_cloud': response.json()['id']
            })
        except Exception:
            pass
        return res
