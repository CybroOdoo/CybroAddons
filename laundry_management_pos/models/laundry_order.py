# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#    you can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import json
from odoo import _, api, fields, models


class LaundryOrder(models.Model):
    """ This class is inherited for model laundry_order.
        It contains fields and the functions for the model

         Methods:
            _compute_amount_all(self):
                Action performs to computing the total amounts of the LaundryOrder.

            _compute_tax_totals_json(self):
                Action performs to computing the total tax amount using the
                order-lines tax and amount.

            _invoice_count(self):
                Action performs to computing the invoice count based on the
                particular Laundry order.

            _work_count(self):
                Action performs to computing the work count based on the
                particular Laundry order.

            Action_view_laundry_works(self):
                Action performs to work details of the LaundryOrder, the
                laundry work smart button views are displayed.

            Action_view_invoice(self):
                Action performs to Invoice details of the LaundryOrder
                when opening the smart button, we can view the invoice details.
    """
    _inherit = 'laundry.order'

    order_ref = fields.Char(string='Order Ref',
                            help='Reference field for order')
    pos_reference = fields.Char(string='Receipt Number',
                                help='Reference field for POS')
    is_invoiced = fields.Boolean(string='Is Invoiced', invisible=1,
                                 help='Boolean field for checking and '
                                      'adding the invoices')
    pos_order = fields.Boolean(string='Is POS order',
                               help='Boolean field for pos order '
                                    'identification')
    pos_order_id = fields.Many2one('pos.order', string='POS order',
                                   help='Relating the many2one field for pos.order')
    tax_totals_json = fields.Char(compute='_compute_tax_totals_json',
                                  string='Total Tax',
                                  help='For computing the tax ')
    amount_untaxed = fields.Monetary(string='Untaxed Amount',
                                     compute='_compute_amount_all',
                                     help='For computing the untaxed amount')
    amount_tax = fields.Monetary(string='Taxes', compute='_compute_amount_all',
                                 help='Compute the tax amounts')
    total_amount = fields.Monetary(string='Total', store=True,
                                   compute='_compute_amount_all',
                                   help='Compute the total amount')

    @api.depends('order_line_ids')
    def _compute_amount_all(self):
        """
        Compute the total amounts of the LaundryOrder.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line_ids:
                amount_untaxed += line.amount
                amount_tax += line.price_tax
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'total_amount': amount_untaxed + amount_tax,
            })

    @api.depends('order_line_ids.tax_ids', 'order_line_ids.amount',
                 'total_amount')
    def _compute_tax_totals_json(self):
        """ computing the total tax amount using the order-lines
        tax and amount"""

        def compute_taxes(order_lines):
            """Compute the taxes for the laundry order lines"""
            price = order_lines.amount
            orders = order_lines.laundry_id
            return order_lines.tax_ids._origin.compute_all(
                price, orders.currency_id,
                product=order_lines.product_id,
                partner=orders.partner_shipping_id)

        for order in self:
            tax_lines_data = self.env[
                'account.move']._prepare_tax_lines_data_for_totals_from_object(
                order.order_lines, compute_taxes)
            tax_totals = self.env['account.move']._get_tax_totals(
                order.partner_id, tax_lines_data, order.order_lines.amount,
                order.total_amount, order.currency_id)
            order.tax_totals_json = json.dumps(tax_totals)

    def _compute_invoice_count(self):
        """Computing the invoice count based on the particular Laundry order"""
        for record in self:
            invoice_count = 0

            # Build search domain based on available references
            if record.order_ref:
                # Check POS order first
                work = self.env['pos.order'].search([('name', '=', record.order_ref)], limit=1)

                if work:
                    # Search by POS order name
                    domain = [('invoice_origin', '=', work.name)]
                else:
                    # Search directly by order_ref
                    domain = [('invoice_origin', '=', record.order_ref)]

                invoice_count = self.env['account.move'].search_count(domain)

            # If no invoice found and sale_id exists, try sale order
            if invoice_count == 0 and hasattr(record, 'sale_id') and record.sale_id:
                invoice_count = self.env['account.move'].search_count(
                    [('invoice_origin', '=', record.sale_id.name)])

            # Alternative: Try searching by ref field as well
            if invoice_count == 0 and record.order_ref:
                invoice_count = self.env['account.move'].search_count(
                    [('ref', '=', record.order_ref)])

            record.invoice_count = invoice_count
            if hasattr(record, 'is_invoiced'):
                record.is_invoiced = invoice_count > 0

    def _work_count(self):
        """Computing the work count based on the particular Laundry order
        override the _work_count function"""
        work = self.env['pos.order'].search(
            [('name', '=', self.order_ref)])
        if not work:
            if self.id:
                self.work_count = self.env['washing.washing'].search_count(
                    [('laundry_id.laundry_id.id', '=', self.id)])
            else:
                self.work_count = False
        else:
            self.work_count = len(work.lines)

    def action_view_invoice(self):
        """
        Invoice details of the LaundryOrder when opening the smart button
        we can view the invoice details.
        """
        # First, let's try to find the invoice directly from the laundry order
        invoice = False

        # Method 1: Search by order_ref in invoice_origin
        if self.order_ref:
            invoice = self.env['account.move'].search(
                [('invoice_origin', '=', self.order_ref)], limit=1)

        # Method 2: If not found, search through POS order
        if not invoice and self.order_ref:
            work = self.env['pos.order'].search(
                [('name', '=', self.order_ref)], limit=1)

            if work:
                # Try searching by POS order name
                invoice = self.env['account.move'].search(
                    [('invoice_origin', '=', work.name)], limit=1)

                # Or try if there's a direct relation
                if not invoice and hasattr(work, 'account_move'):
                    invoice = work.account_move

        # Method 3: If you have a direct invoice_id field in laundry.order
        if not invoice and hasattr(self, 'invoice_id'):
            invoice = self.invoice_id

        if not invoice and hasattr(self, 'sale_id') and self.sale_id:
            action = super().action_view_invoice()
            if action:
                return action

        if invoice:
            view_id = self.env.ref('account.view_move_form').id
            return {
                'view_mode': 'form',
                'res_model': 'account.move',
                'view_id': view_id,
                'type': 'ir.actions.act_window',
                'name': _('Invoice'),
                'res_id': invoice.id,
            }

        # If no invoice found, show a message
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('No Invoice'),
                'message': _('No invoice found for this order: %s') % (self.order_ref or 'N/A'),
                'type': 'warning',
            }
        }

    def action_create_invoice(self):
        """Create invoice for POS orders or fallback to standard order invoice"""
        self.ensure_one()
        if self.pos_order_id:
            if getattr(self.pos_order_id, 'state', '') != 'invoiced':
                res = self.pos_order_id.action_pos_order_invoice()
                # If you need to download or view it, res will contain the action
                self._compute_invoice_count()
                return res
            return True
        else:
            return super().action_create_invoice()
