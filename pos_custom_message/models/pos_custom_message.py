# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

from odoo import api, fields, models


class PosCustomMessage(models.Model):
    """Model to manage custom popup messages for the Point of Sale system."""
    _name = 'pos.custom.message'
    _description = "Custom Popup Messages in Pos Screen"
    _rec_name = 'title'

    message_type = fields.Selection([('alert', 'Alert'),
                                     ('warn', 'Warning'),
                                     ('info', 'Information')], default='alert',
                                    string="Message Type",
                                    help="Choose the message type")
    title = fields.Char(string="Title", help="Title of the message")
    message_text = fields.Char(string="Message Text",
                               help="Content of the message")
    execution_time = fields.Float(string="Execution Time",
                                  help="Choose the time in 24-hour format at "
                                       "which the popup should be shown.")
    pos_config_ids = fields.Many2many('pos.config',
                                      string="Point of sale",
                                      help="Choose the point of sale")

    @api.model
    def _load_pos_data_fields(self, config_id):
        return [
            'id', 'message_type', 'title', 'message_text', 'execution_time', 'pos_config_ids'
        ]

    @api.model
    def _load_pos_data_domain(self, data):
        return []

    def _load_pos_data(self, data):
        domain = self._load_pos_data_domain(data)
        fields = self._load_pos_data_fields(data['pos.config']['data'][0]['id'])
        return {
            'data': self.search_read(domain, fields, load=False) if domain is not False else [],
            'fields': fields,
        }
