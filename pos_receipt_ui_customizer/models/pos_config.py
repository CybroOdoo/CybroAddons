# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import fields, models, api


class PosConfig(models.Model):
    """
        This is an Odoo model for Point of Sale (POS).
        It inherits the 'pos.config' model to add new fields.
    """
    _inherit = 'pos.config'

    receipt_design_id = fields.Many2one('pos.receipt', string='Receipt Design',
                                        help='Choose any receipt design')
    design_receipt = fields.Text(related='receipt_design_id.design_receipt',
                                 string='Receipt XML')
    logo = fields.Binary(related='receipt_design_id.logo', string='Logo',
                         readonly=False)
    is_custom_receipt = fields.Boolean(string='Is Custom Receipt',
                                       help='Indicates the receipt  design is '
                                            'custom or not')
    design_receipt_font_style = fields.Char(
        related='receipt_design_id.design_receipt_font_style',
        string='Receipt Font Style'
    )

    selected_product_fields = fields.Text(
        compute="_compute_selected_product_fields",
        store=True
    )
    enable_qr = fields.Boolean(
        string="Enable Receipt QR",
        related='receipt_design_id.enable_qr',
        readonly=False,
        store=True,
    )
    enable_qr_section = fields.Boolean(
        string="Enable QR Section",
        related='receipt_design_id.enable_qr_section',
        readonly=False,
        store=True,
    )

    receipt_qr_size = fields.Integer(
        string='Receipt QR Code Size',
        related='receipt_design_id.receipt_qr_size',
        readonly=False,
        store=True,
    )

    receipt_qr_position = fields.Selection(
        string='Receipt QR Position',
        related='receipt_design_id.receipt_qr_position',
        readonly=False,
        store=True,
    )

    receipt_bg_color = fields.Char(
        string="Receipt Background Color",
        default="#abc64b"
    )
    receipt_bg_image = fields.Binary("Receipt Background Image")

    @api.depends('receipt_design_id', 'receipt_design_id.selected_product_fields')
    def _compute_selected_product_fields(self):
        """Compute selected product fields from the chosen receipt design."""

        for rec in self:
            if rec.receipt_design_id and rec.receipt_design_id.selected_product_fields:
                rec.selected_product_fields = rec.receipt_design_id.selected_product_fields
            else:
                rec.selected_product_fields = '[]'

    def action_open_receipt_editor(self):
        """Open the POS receipt layout editor for the selected receipt design."""

        self.ensure_one()

        if not self.receipt_design_id:
            return False

        return {
            "type": "ir.actions.client",
            "tag": "pos_receipt_layout_client_action",
            "target": "current",
            "params": {
                "receipt_id": self.receipt_design_id.id,
            }
        }
