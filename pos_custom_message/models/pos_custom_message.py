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
from ast import literal_eval

from odoo import api, fields, models


class PosCustomMessage(models.Model):
    """Model to manage custom popup messages for the Point of Sale system."""
    _name = 'pos.custom.message'
    _description = "Custom Popup Messages in Pos Screen"
    _inherit = ['pos.load.mixin']
    _rec_name = 'title'

    message_type = fields.Selection([('alert', 'Alert'),
                                     ('warn', 'Warning'),
                                     ('info', 'Information')], default='alert',
                                    help="Choose the message type")
    title = fields.Char(help="Title of the message")
    message_text = fields.Char(help="Content of the message")
    execution_time = fields.Float(help="Choose the time in 24-hour format at "
                                       "which the popup should be shown.")
    pos_config_ids = fields.Many2many('pos.config',
                                      string="Point of sale",
                                      help="Choose the point of sale")

    @api.model
    def _get_selected_message_ids(self):
        """Return the message ids selected in the POS settings.

        :return: None when no selection was ever saved (all messages linked
            to the POS are shown), otherwise the list of selected ids that
            still exist (an empty list means no message is shown).
        """
        value = self.env['ir.config_parameter'].sudo().get_str(
            'pos_custom_message.message_ids')
        if not value:
            return None
        try:
            message_ids = literal_eval(value)
        except (ValueError, SyntaxError):
            return None
        if not isinstance(message_ids, (list, tuple)):
            return None
        return self.sudo().browse(
            [mid for mid in message_ids if isinstance(mid, int)]).exists().ids

    @api.model
    def _load_pos_data_domain(self, data):
        """Only load messages that are linked to the current POS config."""
        config = data.get('pos.config')
        domain = [('pos_config_ids', 'in', config.ids)] if config else []
        selected_message_ids = self._get_selected_message_ids()
        if selected_message_ids is not None:
            domain.append(('id', 'in', selected_message_ids))
        return domain

    @api.model
    def _load_pos_data_fields(self, config):
        """Fields to expose to the POS frontend."""
        return ['id', 'message_type', 'title', 'message_text',
                'execution_time', 'pos_config_ids']
