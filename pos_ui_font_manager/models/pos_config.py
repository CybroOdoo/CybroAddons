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


class PosConfig(models.Model):
    """Extend POS settings with configurable interface font sizes."""

    _inherit = 'pos.config'

    pos_font_preset = fields.Selection([
        ('small', 'Small (Compact)'),
        ('medium', 'Medium (Default)'),
        ('large', 'Large'),
        ('extra_large', 'Extra Large'),
        ('custom', 'Custom')
    ], string='Font Preset', default='medium',
       help='Select a font size preset for the POS interface or choose Custom to specify individual font sizes.')
    pos_global_scale = fields.Integer(
        string='Global Scale (%)', default=100,
        help='Global percentage scaling factor for POS interface fonts.')

    # Custom individual font sizes
    pos_product_card_font_size = fields.Integer(
        string='Product Card', default=0,
        help='Font size for product card titles in pixels (0 for default).')
    pos_product_price_font_size = fields.Integer(
        string='Product Price', default=0,
        help='Font size for product prices on cards in pixels (0 for default).')
    pos_categories_font_size = fields.Integer(
        string='Categories', default=0,
        help='Font size for category selection buttons in pixels (0 for default).')
    pos_numpad_font_size = fields.Integer(
        string='Numpad', default=0,
        help='Font size for numpad buttons in pixels (0 for default).')
    pos_order_line_font_size = fields.Integer(
        string='Order Lines', default=0,
        help='Font size for order line items in pixels (0 for default).')
    pos_control_buttons_font_size = fields.Integer(
        string='Control Buttons', default=0,
        help='Font size for action and control buttons in pixels (0 for default).')
    pos_payment_screen_font_size = fields.Integer(
        string='Payment Screen', default=0,
        help='Font size for payment screen elements in pixels (0 for default).')
    pos_payment_total_font_size = fields.Integer(
        string='Payment Total', default=0,
        help='Font size for total amount on the payment screen in pixels (0 for default).')
    pos_receipt_preview_font_size = fields.Integer(
        string='Receipt Preview', default=0,
        help='Font size for receipt preview display in pixels (0 for default).')
    pos_customer_list_font_size = fields.Integer(
        string='Customer List', default=0,
        help='Font size for customer list entries in pixels (0 for default).')
    pos_navbar_font_size = fields.Integer(
        string='Navbar', default=0,
        help='Font size for top navigation bar elements in pixels (0 for default).')
    pos_ticket_screen_font_size = fields.Integer(
        string='Ticket Screen', default=0,
        help='Font size for ticket and orders screen elements in pixels (0 for default).')
    pos_popups_dialogs_font_size = fields.Integer(
        string='Popups & Dialogs', default=0,
        help='Font size for modal popups and dialog windows in pixels (0 for default).')
