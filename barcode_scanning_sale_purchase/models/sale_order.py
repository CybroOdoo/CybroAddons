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


class SaleOrderLine(models.Model):
    """Inherited the model for to add field for barcode."""
    _inherit = 'sale.order.line'

    barcode_scan = fields.Char(string='Product Barcode',
                               help="Here you can provide the barcode for "
                                    "the product")

    @api.onchange('barcode_scan', 'product_template_id')
    def _onchange_barcode_scan(self):
        """Scanning the barcode will automatically add products to order line"""
        product_rec = self.env['product.product']
        if self.barcode_scan:
            product = product_rec.search([('barcode', '=', self.barcode_scan)])
            self.product_id = product.id

    def _prepare_invoice_line(self, **optional_values):
        """Corresponding barcode of product will show in account move"""
        res = super(SaleOrderLine, self)._prepare_invoice_line(
            **optional_values)
        if self.barcode_scan:
            res.update({'barcode_scan': self.barcode_scan})
        return res


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        """Corresponding barcode of product will show in stock picking"""
        res = super().action_confirm()
        for rec in self.order_line:
            self.env['stock.move'].search([('sale_line_id', '=', rec.id)])[
                'barcode_scan'] = rec.barcode_scan
        return res
