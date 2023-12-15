# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models
from odoo.tools import float_is_zero


class SaleOrder(models.Model):
    """Inherits the sale order for selecting products for updating the
    invoice-able vals"""
    _inherit = 'sale.order'

    def action_select_all(self):
        """Select all the products from the sale order line for invoice"""
        self.order_line.filtered(lambda rec: rec.qty_to_invoice > 0).write(
            {'is_product_select': True})

    def action_deselect_all(self):
        """ Deselect all the products from the sale order line for invoice"""
        self.order_line.filtered(lambda rec: rec.qty_to_invoice > 0).write(
            {'is_product_select': False})

    def _get_invoiceable_lines(self, final=False):
        """Return the invoice-able lines for order `self` and Update the
         invocable lines on the basis of selected lines"""
        down_payment_line_ids = []
        invoiceable_line_ids = []
        pending_section = None
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        selected_lines = []
        for line in self.order_line:
            if (line.is_product_select or line.is_downpayment) or \
                    True not in self.order_line.mapped('is_product_select'):
                selected_lines.append(line)
                if line.display_type == 'line_section':
                    # Only invoice the section if one of its lines is
                    # invoice-able
                    pending_section = line
                    continue
                if line.display_type != 'line_note' and float_is_zero(
                        line.qty_to_invoice, precision_digits=precision):
                    continue
                if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0
                                               and final) or \
                        line.display_type == 'line_note':
                    if line.is_downpayment:
                        # Keep down payment lines separately, to put them
                        # together at the end of the invoice, in a specific
                        # dedicated section.
                        down_payment_line_ids.append(line.id)
                        continue
                    if pending_section:
                        invoiceable_line_ids.append(pending_section.id)
                        pending_section = None
                    invoiceable_line_ids.append(line.id)
            else:
                line.is_product_select = True
        return self.env['sale.order.line'].browse(invoiceable_line_ids +
                                                  down_payment_line_ids)


class SaleOrderLine(models.Model):
    """Inherits the sale order line for selecting the order line"""
    _inherit = 'sale.order.line'

    is_product_select = fields.Boolean(string="Select", copy=False,
                                       help="Select products from order line")
