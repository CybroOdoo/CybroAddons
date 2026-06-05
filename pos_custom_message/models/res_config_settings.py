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

from ast import literal_eval
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Inherited the res.config.settings model to add a field to select the
    messages"""
    _inherit = 'res.config.settings'

    message_ids = fields.Many2many('pos.custom.message',
                                   string="Messages to popup", related="pos_config_id.message_ids",
                                   help="Choose the messages to show as popup", readonly=False, ondelete='cascade')

    def set_values(self):
        """
        Override the 'set_values' method to save the selected messages as
        configuration parameters.
        """
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'pos_custom_message.message_ids', self.message_ids.ids)
        return res

    @api.model
    def get_values(self):
        """
        Override the 'get_values' method to retrieve the selected messages from
        configuration parameters.
        """
        res = super(ResConfigSettings, self).get_values()
        selected_message_ids = self.env['ir.config_parameter'].sudo(
        ).get_param('pos_custom_message.message_ids')
        res.update(message_ids=[
            (6, 0, literal_eval(selected_message_ids))] if selected_message_ids
        else False)
        return res
