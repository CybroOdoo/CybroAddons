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
    _inherit = 'pos.config'

    pos_font_preset = fields.Selection([
        ('small', 'Small (Compact)'),
        ('medium', 'Medium (Default)'),
        ('large', 'Large'),
        ('extra_large', 'Extra Large'),
        ('custom', 'Custom')
    ], string='Font Preset', default='medium')
    pos_global_scale = fields.Integer(string='Global Scale (%)', default=100)

    # Custom individual font sizes
    pos_product_card_font_size = fields.Integer(string='Product Card', default=0)
    pos_product_price_font_size = fields.Integer(string='Product Price', default=0)
    pos_categories_font_size = fields.Integer(string='Categories', default=0)
    pos_numpad_font_size = fields.Integer(string='Numpad', default=0)
    pos_order_line_font_size = fields.Integer(string='Order Lines', default=0)
    pos_control_buttons_font_size = fields.Integer(string='Control Buttons', default=0)
    pos_payment_screen_font_size = fields.Integer(string='Payment Screen', default=0)
    pos_payment_total_font_size = fields.Integer(string='Payment Total', default=0)
    pos_receipt_preview_font_size = fields.Integer(string='Receipt Preview', default=0)
    pos_customer_list_font_size = fields.Integer(string='Customer List', default=0)
    pos_navbar_font_size = fields.Integer(string='Navbar', default=0)
    pos_ticket_screen_font_size = fields.Integer(string='Ticket Screen', default=0)
    pos_popups_dialogs_font_size = fields.Integer(string='Popups & Dialogs', default=0)
