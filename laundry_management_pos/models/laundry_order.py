# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Unnimaya C O (odoo@cybrosys.com)
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
    """ This class is inherited for model laundry_order.
        It contains fields and the functions for the model

         Methods:
            _compute_amount_all(self):
                Action perform to computing the total amounts of the LaundryOrder.

            _compute_tax_totals_json(self):
                Action perform to computing the total tax amount using the order-lines tax and amount.

            _invoice_count(self):
                Action perform to computing the invoice count based on the particular Laundry order.

            _work_count(self):
                Action perform to computing the work count based on the particular Laundry order.

            action_view_laundry_works(self):
                Action perform to works details of the LaundryOrder , the laundry work smart button views are displayed.

            action_view_invoice(self):
                Action perform to Invoice details of the LaundryOrder when opening the smart button we can view the invoice details.
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
                                  help='For computing the tax ')
    amount_untaxed = fields.Monetary(string='Untaxed Amount',
                                     compute='_compute_amount_all',
                                     help='For computing the untaxed amount')
    amount_tax = fields.Monetary(string='Taxes', compute='_compute_amount_all',
                                 help='Compute the tax amounts')
    total_amount = fields.Monetary(string='Total', store=True,
                                   compute='_compute_amount_all',
                                   help='Compute the total amount')

    @api.depends('order_lines')
    def _compute_amount_all(self):
        """
        Compute the total amounts of the LaundryOrder.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_lines:
                amount_untaxed += line.amount
                amount_tax += line.price_tax
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'total_amount': amount_untaxed + amount_tax,
            })

    @api.depends('order_lines.tax_ids', 'order_lines.amount',
                 'total_amount')
    def _compute_tax_totals_json(self):
        """ computing the total tax amount using the order-lines
        tax and amount"""
        def compute_taxes(order_lines):
            price = order_lines.amount
            orders = order_lines.laundry_obj
            return order_lines.tax_ids._origin.compute_all(price,
                                                           orders.currency_id,
                                                           product=
                                                           order_lines.product_id,
                                                           partner=
                                                           orders.partner_shipping_id)

        for order in self:
            tax_lines_data = self.env['account.move']._prepare_tax_lines_data_for_totals_from_object(
                order.order_lines, compute_taxes)
            tax_totals = self.env['account.move']._get_tax_totals(
                order.partner_id, tax_lines_data, order.order_lines.amount,
                order.total_amount, order.currency_id)
            order.tax_totals_json = json.dumps(tax_totals)

    def _invoice_count(self):
        """Computing the invoice count based on the particular Laundry order
         override the _invoice_count function"""
        work = self.env['pos.order'].search(
            [('name', '=', self.order_ref)])
        if not work:
            wrk_ordr_ids = self.env['account.move'].search([('invoice_origin', '=',
                                                             self.sale_obj.name)])
            self.invoice_count = len(wrk_ordr_ids)
        else:
            work_orders = self.env['account.move'].search([('invoice_origin',
                                                            '=', work.name)])
            self.invoice_count = len(work_orders)
            self.is_invoiced = True

    def _work_count(self):
        """Computing the work count based on the particular Laundry order
        override the _work_count function"""
        work = self.env['pos.order'].search(
            [('name', '=', self.order_ref)])
        if not work:
            if self.id:
                wrk_ordr_ids = self.env['washing.washing'].search([('laundry_obj.laundry_obj.id', '=', self.id)])
                self.work_count = len(wrk_ordr_ids)
            else:
                self.work_count = False
        else:
            self.work_count = len(work.lines)

    def action_view_laundry_works(self):
        """
            works details of the LaundryOrder , the laundry work
             smart button views are displayed here.
        """
        result = super().action_view_laundry_works()
        pos_orders = self.env['pos.order'].search(
            [('name', '=', self.order_ref)])
        pos_order_ids = pos_orders.mapped('id')
        view_id = self.env.ref('laundry_management.washing_form_view').id
        if pos_orders and len(pos_orders.lines) <= 1:
            return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'washing.washing',
                'view_id': view_id,
                'type': 'ir.actions.act_window',
                'name': _('Works'),
                'res_id': pos_order_ids and pos_order_ids[0]
            }

        return result

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


class LaundryOrderLine(models.Model):
    """ This class is inherited for model laundry_order_line.
            It contains fields and the functions for the model

        Methods:
            _compute_price_tax(self):
                Action perform to compute the subtotal amounts of the LaundryOrder line.

    """
    _inherit = 'laundry.order.line'

    # washing_type field is updated with the module Laundry Management
    washing_type = fields.Many2one('washing.type', string='Washing Type',
                                   required=False,
                                   help='The many2one field for relating'
                                        ' to the washing type')
    tax_ids = fields.Many2many('account.tax', string='Taxes',
                               help='The many2one field for relating to '
                                    'the account tax')
    price_tax = fields.Float(compute='_compute_price_tax', string='Total Tax',
                             help='The compute field for calculating price '
                                  'tax')

    @api.depends('qty', 'washing_type', 'extra_work', 'tax_ids')
    def _compute_price_tax(self):
        """
        Compute the amounts of the LaundryOrder line ie used to calculate subtotal amount with the quantity of product and the washing types.
        """
        for line in self:
            price = line.washing_type.amount
            taxes = line.tax_ids.compute_all(price,
                                             line.laundry_obj.currency_id,
                                             line.qty,
                                             product=line.product_id,
                                             partner=line.laundry_obj.partner_shipping_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
            })
