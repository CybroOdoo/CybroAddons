###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
from odoo import api, fields, models
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    """Inherits the sale order line for adding the boolean field"""
    _inherit = 'sale.order.line'

    is_product_select = fields.Boolean(
        string="Select",
        help="To Select products from order line",
        copy=False)


class SaleOrder(models.Model):
    """Inherits the sale order for selecting products"""
    _inherit = 'sale.order'

    is_qty_to_invoice = fields.Boolean(
        help="Is any pending qty to invoice",
        compute='_compute_is_qty_to_invoice')

    @api.depends('order_line.is_product_select', 'order_line.qty_to_invoice')
    def _compute_is_qty_to_invoice(self):
        """Hide the Select All / Deselect All buttons when there is nothing
        to select, or when every invoiceable line is already selected."""
        for order in self:
            selectable = order.order_line.filtered(
                lambda line: line.qty_to_invoice > 0)
            order.is_qty_to_invoice = (
                not selectable
                or all(selectable.mapped('is_product_select')))

    def action_select_all(self):
        """Select all the products from the sale order line for invoice"""
        self.order_line.filtered(lambda rec: rec.qty_to_invoice > 0).write(
            {'is_product_select': True})

    def action_deselect_all(self):
        """ Deselect all the products from the sale order line for invoice"""
        self.order_line.filtered(lambda rec: rec.qty_to_invoice > 0).write(
            {'is_product_select': False})

    def _get_invoiceable_lines(self, final=False):
        """Extend the standard invoiceable lines so that only the lines the
        user selected are invoiced.

        The standard method decides which lines are invoiceable; we only
        narrow that result down to the selected lines, so other modules
        overriding this method keep working."""
        lines = super()._get_invoiceable_lines(final=final)
        if not lines:
            # Nothing to invoice at all: let the standard error be raised.
            return lines
        # Only lines that still have something to invoice are in ``lines``,
        # so an already invoiced line with an old selection is ignored.
        selected = lines.filtered(
            lambda line: line.is_product_select and not line.display_type
            and not line.is_downpayment)
        if not selected:
            raise UserError(self.env._(
                "There is no invoiceable line. Please make sure that an "
                "order line is selected"))
        # Keep the selected lines, the down payments, and only the sections,
        # subsections and notes that belong to a selected line.
        kept = self.env['sale.order.line']
        headings = self.env['sale.order.line']
        note_allowed = False
        for line in lines:
            if line.is_downpayment:
                kept |= line
            elif line.display_type == 'line_section':
                headings = line
                note_allowed = False
            elif line.display_type == 'line_subsection':
                headings = headings.filtered(
                    lambda head: head.display_type == 'line_section') | line
                note_allowed = False
            elif line.display_type == 'line_note':
                if note_allowed:
                    kept |= line
            elif line.is_product_select:
                kept |= headings | line
                headings = self.env['sale.order.line']
                note_allowed = True
            else:
                note_allowed = False
        return kept

    def _create_invoices(self, *args, **kwargs):
        """Clear the selection once the invoice is created, so the lines do
        not stay selected for the next invoicing."""
        moves = super()._create_invoices(*args, **kwargs)
        self.order_line.filtered('is_product_select').write(
            {'is_product_select': False})
        return moves
