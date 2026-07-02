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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_font_preset = fields.Selection(related='pos_config_id.pos_font_preset', readonly=False)
    pos_global_scale = fields.Integer(related='pos_config_id.pos_global_scale', readonly=False)
    pos_product_card_font_size = fields.Integer(related='pos_config_id.pos_product_card_font_size', readonly=False)
    pos_product_price_font_size = fields.Integer(related='pos_config_id.pos_product_price_font_size', readonly=False)
    pos_categories_font_size = fields.Integer(related='pos_config_id.pos_categories_font_size', readonly=False)
    pos_numpad_font_size = fields.Integer(related='pos_config_id.pos_numpad_font_size', readonly=False)
    pos_order_line_font_size = fields.Integer(related='pos_config_id.pos_order_line_font_size', readonly=False)
    pos_control_buttons_font_size = fields.Integer(related='pos_config_id.pos_control_buttons_font_size', readonly=False)
    pos_payment_screen_font_size = fields.Integer(related='pos_config_id.pos_payment_screen_font_size', readonly=False)
    pos_payment_total_font_size = fields.Integer(related='pos_config_id.pos_payment_total_font_size', readonly=False)
    pos_receipt_preview_font_size = fields.Integer(related='pos_config_id.pos_receipt_preview_font_size', readonly=False)
    pos_customer_list_font_size = fields.Integer(related='pos_config_id.pos_customer_list_font_size', readonly=False)
    pos_navbar_font_size = fields.Integer(related='pos_config_id.pos_navbar_font_size', readonly=False)
    pos_ticket_screen_font_size = fields.Integer(related='pos_config_id.pos_ticket_screen_font_size', readonly=False)
    pos_popups_dialogs_font_size = fields.Integer(related='pos_config_id.pos_popups_dialogs_font_size', readonly=False)
