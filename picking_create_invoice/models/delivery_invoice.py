# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Treesa Maria(<https://www.cybrosys.com>)
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
###################################################################################
from odoo.exceptions import UserError
from odoo import fields, models, api, _
from odoo.tools import float_is_zero


class CustomerInvoice(models.Model):
    _inherit = 'res.partner'

    invoice_option = fields.Selection([('on_delivery', 'Delivered quantities'),
                                       ('before_delivery', 'Ordered quantities'), ],
                                      "Invoicing Policy")


class DeliveryInvoice(models.Model):

    _inherit = 'sale.order'

    invoice_option = fields.Selection([('on_delivery', 'Delivered quantities'),
                                       ('before_delivery', 'Ordered quantities'), ],
                                      string="Invoicing Policy")

    @api.onchange('partner_id')
    def onchange_customer(self):
        if self.partner_id.invoice_option:
            self.invoice_option = self.partner_id.invoice_option
        else:
            self.invoice_option = False

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        if self.invoice_option == 'before_delivery':
            inv_obj = self.env['account.invoice']
            for order in self:
                inv_data = order._prepare_invoice()
                invoice = inv_obj.create(inv_data)
                for inv_line in order.order_line:

                    inv_line.invoice_line_create(invoice.id, inv_line.product_uom_qty)

        else:
            inv_obj = self.env['account.invoice']
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            invoices = {}
            references = {}
            for order in self:
                group_key = order.id if grouped else (order.partner_invoice_id.id, order.currency_id.id)
                for line in order.order_line.sorted(key=lambda l: l.qty_to_invoice < 0):
                    if float_is_zero(line.qty_to_invoice, precision_digits=precision):
                        continue
                    if group_key not in invoices:

                        inv_data = order._prepare_invoice()
                        invoice = inv_obj.create(inv_data)

                        references[invoice] = order
                        invoices[group_key] = invoice
                    elif group_key in invoices:
                        vals = {}
                        if order.name not in invoices[group_key].origin.split(', '):

                            vals['origin'] = invoices[group_key].origin + ', ' + order.name
                        if order.client_order_ref and order.client_order_ref \
                                not in invoices[group_key].name.split(', '):

                            vals['name'] = invoices[group_key].name + ', ' + order.client_order_ref
                        invoices[group_key].write(vals)
                    if line.qty_to_invoice > 0:
                        line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)
                    elif line.qty_to_invoice < 0 and final:
                        line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)

                if references.get(invoices.get(group_key)):

                    if order not in references[invoices[group_key]]:

                        references[invoice] = references[invoice] | order
            if not invoices:

                raise UserError(_('There is no invoicable line.'))

            for invoice in invoices.values():

                if not invoice.invoice_line_ids:

                    raise UserError(_('There is no invoicable line.'))
                # If invoice is negative, do a refund invoice instead
                if invoice.amount_untaxed < 0:

                    invoice.type = 'out_refund'
                    for line in invoice.invoice_line_ids:

                        line.quantity = -line.quantity
                for line in invoice.invoice_line_ids:

                    line._set_additional_fields(invoice)
                invoice.compute_taxes()
                invoice.message_post_with_view('mail.message_origin_link',
                                               values={'self': invoice, 'origin': references[invoice]},
                                               subtype_id=self.env.ref('mail.mt_note').id)
            return [inv.id for inv in invoices.values()]


class InvoiceControl(models.Model):

    _inherit = 'stock.picking'

    invoice_control = fields.Selection([('to_invoice', 'To be Invoiced'),
                                        ('invoice_na', 'Not applicable'), ],
                                       string="Invoicing Policy", compute='get_invoice_control')

    @api.depends('group_id')
    def get_invoice_control(self):
        for group in self:

            obj = self.env['sale.order'].search([('name', '=', group.group_id.name)])

            if obj.invoice_option == 'on_delivery':
                group.invoice_control = 'to_invoice'
            elif obj.invoice_option == 'before_delivery':
                group.invoice_control = 'invoice_na'
            else:
                group.invoice_control = False

    @api.depends('group_id')
    def pick_create_invoices(self):

                sale_orders = self.env['sale.order'].search([('name', '=', self.group_id.name)])
                sale_orders.action_invoice_create()
                return sale_orders.action_view_invoice()
