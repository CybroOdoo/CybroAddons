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
    """Expose POS interface font settings in the configuration wizard."""

    _inherit = 'res.config.settings'

    pos_font_preset = fields.Selection(
        related='pos_config_id.pos_font_preset', readonly=False,
        help='Select a font size preset for the POS interface or choose Custom to specify individual font sizes.')
    pos_global_scale = fields.Integer(
        related='pos_config_id.pos_global_scale', readonly=False,
        help='Global percentage scaling factor for POS interface fonts.')
    pos_product_card_font_size = fields.Integer(
        related='pos_config_id.pos_product_card_font_size', readonly=False,
        help='Font size for product card titles in pixels (0 for default).')
    pos_product_price_font_size = fields.Integer(
        related='pos_config_id.pos_product_price_font_size', readonly=False,
        help='Font size for product prices on cards in pixels (0 for default).')
    pos_categories_font_size = fields.Integer(
        related='pos_config_id.pos_categories_font_size', readonly=False,
        help='Font size for category selection buttons in pixels (0 for default).')
    pos_numpad_font_size = fields.Integer(
        related='pos_config_id.pos_numpad_font_size', readonly=False,
        help='Font size for numpad buttons in pixels (0 for default).')
    pos_order_line_font_size = fields.Integer(
        related='pos_config_id.pos_order_line_font_size', readonly=False,
        help='Font size for order line items in pixels (0 for default).')
    pos_control_buttons_font_size = fields.Integer(
        related='pos_config_id.pos_control_buttons_font_size', readonly=False,
        help='Font size for action and control buttons in pixels (0 for default).')
    pos_payment_screen_font_size = fields.Integer(
        related='pos_config_id.pos_payment_screen_font_size', readonly=False,
        help='Font size for payment screen elements in pixels (0 for default).')
    pos_payment_total_font_size = fields.Integer(
        related='pos_config_id.pos_payment_total_font_size', readonly=False,
        help='Font size for total amount on the payment screen in pixels (0 for default).')
    pos_receipt_preview_font_size = fields.Integer(
        related='pos_config_id.pos_receipt_preview_font_size', readonly=False,
        help='Font size for receipt preview display in pixels (0 for default).')
    pos_customer_list_font_size = fields.Integer(
        related='pos_config_id.pos_customer_list_font_size', readonly=False,
        help='Font size for customer list entries in pixels (0 for default).')
    pos_navbar_font_size = fields.Integer(
        related='pos_config_id.pos_navbar_font_size', readonly=False,
        help='Font size for top navigation bar elements in pixels (0 for default).')
    pos_ticket_screen_font_size = fields.Integer(
        related='pos_config_id.pos_ticket_screen_font_size', readonly=False,
        help='Font size for ticket and orders screen elements in pixels (0 for default).')
    pos_popups_dialogs_font_size = fields.Integer(
        related='pos_config_id.pos_popups_dialogs_font_size', readonly=False,
        help='Font size for modal popups and dialog windows in pixels (0 for default).')
