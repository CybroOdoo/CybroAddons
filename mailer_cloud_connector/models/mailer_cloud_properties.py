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
#############################################################################
import json
import logging
import requests
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class MailerCloudProperties(models.Model):
    """
    Model representing properties in Mailercloud associated with Odoo records.
    """
    _name = 'mailer.cloud.properties'
    _description = 'Mailercloud Properties'

    mailer_cloud = fields.Char(
        string='Mailercloud',
        help="Mailercloud property identifier.")
    name = fields.Char(
        string='Property Name', required=True,
        help="Name of the Mailercloud property.")
    type = fields.Selection(
        [
            ('text', 'Text'),
            ('number', 'Number'),
            ('date', 'Date'),
            ('textarea', 'Textarea')
        ],
        required=True,
        help="Type of the Mailercloud property.")
    authorization_id = fields.Many2one(
        'mailer.cloud.api.sync', ondelete='cascade',
        help="Authorization associated with this property.")

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override the create method to synchronize property creation with Mailercloud.

        :param vals_list: List of dictionaries of values for creating records.
        :return: Newly created recordset.
        """
        res = super().create(vals_list)
        for record in res:
            if not record.mailer_cloud and record.authorization_id and record.authorization_id.api_key:
                try:
                    url = "https://cloudapi.mailercloud.com/v1/contact/property"
                    payload = json.dumps({
                        "name": record.name,
                        "type": record.type
                    })
                    headers = {
                        'Authorization': record.authorization_id.api_key,
                        'Content-Type': 'application/json'
                    }
                    response = requests.request(
                        "POST", url, headers=headers, data=payload, timeout=30)
                    if response.status_code == 200 and 'id' in response.json():
                        record.write({
                            'mailer_cloud': response.json()['id']
                        })
                except Exception as e:
                    _logger.warning("Failed to create Mailercloud property: %s", e)
        return res
