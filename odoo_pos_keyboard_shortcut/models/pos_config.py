# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
################################################################################
from odoo import fields, models


class PosConfig(models.Model):
    """inherited the pos config model and add new fields"""
    _inherit = 'pos.config'

    is_enable_keyboard_shortcuts = fields.Boolean(
        string='Keyboard shortcuts',
        help='Enable the feature for keyboard shortcuts '
             'using on the point of sale')
    select_shortcut_id = fields.Many2one(
        'pos.keyboard.shortcut',
        string='Choose Shortcut', help='To select pos keyboard shortcut',
    )

    # Direct related fields for instant synchronous access in POS frontend
    shortcut_customer_screen = fields.Char(related='select_shortcut_id.customer_screen',string="Customer Screen Shortcut",help="Shortcut for Customer screen")
    shortcut_next_screen = fields.Char(related='select_shortcut_id.next_screen',string="Next Screen Shortcut",help="Shortcut for Next screen")
    shortcut_select_qty = fields.Char(related='select_shortcut_id.select_qty',string="Quantity Selection Shortcut",help="Shortcut For Selecting Quantity")
    shortcut_select_discount = fields.Char(related='select_shortcut_id.select_discount',string="Discount Selection Shortcut",help="Shortcut For Selecting Discount")
    shortcut_select_price = fields.Char(related='select_shortcut_id.select_price',string="Price Selection Discount",help="Shortcut For Selecting Price")
    shortcut_print_receipt = fields.Char(related='select_shortcut_id.print_receipt',string="Print Receipt Shortcut",help="Shortcut For Printing Receipt")
    shortcut_back_screen = fields.Char(related='select_shortcut_id.back_screen',string="Back Screen Shortcut",help="Shortcut For Back Screen")
    shortcut_select_user = fields.Char(related='select_shortcut_id.select_user',string="User Selection Shortcut",help="Shortcut For Selecting User")
    shortcut_sent_email = fields.Char(related='select_shortcut_id.sent_email',string="Send Email Shortcut",help="Shortcut For Sending Email")
    shortcut_resume_order = fields.Char(related='select_shortcut_id.resume_order',string="Resume Order Shortcut",help="Shortcut For Resuming Order")
    shortcut_new_order = fields.Char(related='select_shortcut_id.new_order',string="New Order Shortcut",help="Shortcut For New Order")
    shortcut_close_pos = fields.Char(related='select_shortcut_id.close_pos',string="Close Pos Shortcut",help="Shortcut For Closing Pos")
    shortcut_select_invoice = fields.Char(related='select_shortcut_id.select_invoice',string="Invoice Selection Shortcut",help="Shortcut For Selecting Invoice")
    shortcut_validate_order = fields.Char(related='select_shortcut_id.validate_order',string="Order Validation Shortcut",help="Shortcut For Validating Order")
    shortcut_click_ok = fields.Char(related='select_shortcut_id.click_ok',string="Ok Shortcut",help="Shortcut To Click Ok")
    shortcut_click_cancel = fields.Char(related='select_shortcut_id.click_cancel',string="Cancel Shortcut",help="Shortcut To Cancel")
    shortcut_next_screen_show = fields.Char(related='select_shortcut_id.next_screen_show',string="Next Screen Shortcut",help="Shortcut To Next Screen")
    shortcut_delete_orderlines = fields.Char(related='select_shortcut_id.delete_orderlines',string="Delete Orderline Shortcut",help="Shortcut To Delete Orderlines")