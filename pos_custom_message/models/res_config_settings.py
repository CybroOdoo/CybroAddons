# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Inherited the res.config.settings model to add a field to select the
    messages"""
    _inherit = 'res.config.settings'

    message_ids = fields.Many2many(
        'pos.custom.message', string="Messages to popup",
        domain="[('pos_config_ids', 'in', pos_config_id)]",
        help="Choose the messages to show as popup")

    def set_values(self):
        """Save the selected messages as a configuration parameter."""
        res = super().set_values()
        self.env['ir.config_parameter'].sudo().set_str(
            'pos_custom_message.message_ids', str(self.message_ids.ids))
        return res

    @api.model
    def get_values(self):
        """Load the selected messages from the configuration parameter.

        Messages that were deleted since they were selected are ignored.
        """
        res = super().get_values()
        selected_message_ids = self.env[
            'pos.custom.message']._get_selected_message_ids()
        res.update(message_ids=[fields.Command.set(selected_message_ids)]
                   if selected_message_ids else False)
        return res
