# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sreejith P (<https://www.cybrosys.com>)
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
#############################################################################
from odoo import api, fields, models


class PurchaseOrderLines(models.Model):
    """Inherited the model for add field for barcode."""
    _inherit = "purchase.order.line"

    barcode_scan = fields.Char(string='Product Barcode',
                               help="Here you can provide the barcode for the "
                                    "product")

    @api.onchange('barcode_scan')
    def _onchange_barcode_scan(self):
        """Scanning the barcode will automatically add products to order line"""
        product_rec = self.env['product.product']
        if self.barcode_scan:
            product = product_rec.search([('barcode', '=', self.barcode_scan)])
            self.product_id = product.id


class PurchaseOrder(models.Model):
    """Added functions for pass the values from the order line to stock picking
    and account move"""
    _inherit = 'purchase.order'

    def button_confirm(self):
        """Corresponding barcode of product will show in stock picking"""
        res = super().button_confirm()
        for rec in self.order_line:
            self.env['stock.move'].search([('purchase_line_id', '=', rec.id)])[
                'barcode_scan'] = rec.barcode_scan
        return res

    def action_create_invoice(self):
        """Corresponding barcode of product will show in account move line"""
        res = super().action_create_invoice()
        for rec in self.order_line:
            self.env['account.move.line'].search(
                [('purchase_line_id', '=', rec.id)])[
                'barcode_scan'] = rec.barcode_scan
        return res
