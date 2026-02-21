# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nubla Sherin k (<https://www.cybrosys.com>)
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
from odoo import fields, models


class PosReceipt(models.Model):
    """
        This is an Odoo model for Point of Sale (POS).
        It creates a new model of pos.receipt for providing different types of
        receipt design.
    """
    _name = 'pos.receipt'
    _description = 'POS Receipts'

    name = fields.Char(string='Name', help='Name of the pos receipt')
    design_receipt = fields.Text(string='Receipt XML',
                                 help='Add your customised receipts for pos')
    design_receipt_font_style = fields.Char(string="Font Style", default="Arial")
    company_id = fields.Many2one('res.company', string='Company', readonly=True, index=True, required=True,
                                 default=lambda self: self.env.company)
    logo = fields.Binary(string='Logo', default=lambda self: self.env.company.logo)
    selected_product_fields = fields.Text(
        string="Selected Product Fields",
        help="JSON list of product fields to show as receipt columns",
        default='[]'
    )
    selected_columns_config = fields.Text(
        default="[]",
        help="Receipt column layout configuration"
    )

    enable_qr = fields.Boolean(
        string="Enable Receipt QR",
        default=False
    )
    enable_qr_section = fields.Boolean(
        string="Enable QR Section",
        default=False
    )

    qr_size = fields.Integer(
        string='URL QR Code Size',
        default=120,
        help='Size of the URL QR code in pixels (80-300px)'
    )

    qr_position = fields.Selection([
        ('left', 'Left'),
        ('center', 'Center'),
        ('right', 'Right')
    ], string='URL QR Position', default='center',
        help='Alignment position for the URL QR code')

    receipt_qr_size = fields.Integer(
        string='Receipt QR Code Size',
        default=120,
        help='Size of the receipt QR code in pixels (80-300px)'
    )

    receipt_qr_position = fields.Selection([
        ('left', 'Left'),
        ('center', 'Center'),
        ('right', 'Right')
    ], string='Receipt QR Position', default='center',
        help='Alignment position for the receipt QR code')


    def action_open_receipt_layout(self):
        self.ensure_one()
        return {
            "type": "ir.actions.client",
            "tag": "pos_receipt_layout_client_action",
            "target": "current",
            "params": {
                "receipt_id": self.id,
            }
        }