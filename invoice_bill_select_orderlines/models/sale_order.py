# -*- coding: utf-8 -*-
"""
Can use only selected products to invoice as well as bills.
"""
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class SaleOrderLine(models.Model):
    """Inherits the sale order line for adding the boolean field"""
    _inherit = 'sale.order.line'

    is_product_select = fields.Boolean(string="Select",
                                       help="To Select products from order line",
                                       copy=False)


class SaleOrder(models.Model):
    """Inherits the sale order for selecting products"""
    _inherit = 'sale.order'

    is_qty_to_invoice = fields.Boolean(string="Is Qty To Invoice",
                                       help="Is any pending qty to invoice",
                                       compute='_compute_is_qty_to_to_invoice')

    def _compute_is_qty_to_to_invoice(self):
        """Function to hide the select/deselect button when nothing to
         invoice"""
        if self.invoice_status == 'no':
            self.is_qty_to_invoice = True
        elif False in self.order_line.mapped('is_product_select'):
            self.is_qty_to_invoice = False
        else:
            self.is_qty_to_invoice = True

    def action_select_all(self):
        """Select all the products from the sale order line for invoice"""
        self.order_line.filtered(lambda rec: rec.qty_to_invoice > 0).write(
            {'is_product_select': True})

    def action_deselect_all(self):
        """ Deselect all the products from the sale order line for invoice"""
        self.order_line.filtered(lambda rec: rec.qty_to_invoice > 0).write(
            {'is_product_select': False})

    def _get_invoiceable_lines(self, line_section='line_section'):
        """Return the invoice-able lines for order `self` and Update the
         invoiceable lines on the basis of selected lines"""
        if self.order_line.filtered(
                lambda line: line.is_product_select):
            down_payment_line_ids = []
            invoiceable_line_ids = []
            precision = self.env['decimal.precision'].precision_get(
                'Product Unit of Measure')
            selected_lines = []
            for line in self.order_line.filtered(lambda line_select: (
                                                                             line_select.is_product_select or line_select.is_downpayment) or
                                                                     True not in self.order_line.mapped(
                'is_product_select') or line_select.display_type == 'line_section' or line_select.display_type == 'line_note'):
                selected_lines.append(line)
                if line.display_type == line_section:
                    # Add the section to the invoiceable lines
                    invoiceable_line_ids.append(line.id)
                elif line.display_type == 'line_note':
                    # Add the note to the invoiceable lines
                    invoiceable_line_ids.append(line.id)
                elif float_is_zero(line.qty_to_invoice,
                                   precision_digits=precision):
                    continue
                else:
                    invoiceable_line_ids.append(line.id)
            # Add the down payment lines to the invoiceable lines, at the end
            invoiceable_line_ids += down_payment_line_ids
            return self.env['sale.order.line'].browse(invoiceable_line_ids)
        raise UserError(_('There is no invoiceable line. Please make sure '
                          'that a order line is selected'))
