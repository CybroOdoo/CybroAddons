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
from odoo import api, fields, models, _


class LaundryOrder(models.Model):
    """
    Inherits the laundry.order model to add POS integration fields and
    functionality for tracking POS orders and computing taxes.
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
                                  help='Technical field to store the tax totals in JSON format')
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
            """
            Compute the taxes for the given order lines.
            """
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
        """Computing the invoice count based on the particular Laundry order
         override the _invoice_count function"""
        work = self.env['pos.order'].search(
            [('name', '=', self.order_ref)])
        if not work:
            self.invoice_count = self.env['account.move'].search_count(
                [('invoice_origin', '=',
                  self.sale_obj.name)])
        else:
            self.invoice_count = self.env['account.move'].search_count([('invoice_origin',
                                                                         '=', work.name)])
            self.is_invoiced = True

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
        result = super(LaundryOrder, self).action_view_invoice()
        work = self.env['pos.order'].search(
            [('name', '=', self.order_ref)])
        invoice = self.env['account.move'].search(
            [('invoice_origin', '=', work.name)])
        invoice_ids = invoice.mapped('id')
        view_id = self.env.ref('account.view_move_form').id
        if invoice and len(invoice_ids) <= 1:
            return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.move',
                'view_id': view_id,
                'type': 'ir.actions.act_window',
                'name': _('Invoice'),
                'res_id': invoice_ids and invoice_ids[0]
            }
        return result
