# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#     Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#     Author: Anaswara S (odoo@cybrosys.com)
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
###############################################################################
from datetime import datetime
from odoo import api, Command, fields, models, _
from odoo.exceptions import ValidationError


class LaundryOrder(models.Model):
    """laundry orders generating model"""
    _name = 'laundry.order'
    _inherit = 'mail.thread'
    _description = "Laundry Order"
    _order = 'order_date desc, id desc'

    name = fields.Char(string="Label", copy=False, help="Name of the record")
    sale_id = fields.Many2one('sale.order',
                              help="sequence name of sale order")
    invoice_status = fields.Selection(string='Invoice Status', related='sale_id.invoice_status',
        store=True, help="Status of invoice")
    invoice_count = fields.Integer(compute='_compute_invoice_count',
                                   string='#Invoice',
                                   help="Number of invoice count")
    work_count = fields.Integer(compute='_compute_work_count', string='# Works',
                                help="Number of work count")
    partner_id = fields.Many2one('res.partner', string='Customer',
                                 readonly=True,
                                 required=True,
                                 change_default=True, index=True,
                                 help="Name of customer"
                                 )
    partner_invoice_id = fields.Many2one('res.partner',
                                         string='Invoice Address',
                                         store=True,
                                         readonly=False, required=True,
                                         compute='_compute_partner_invoice_id',
                                         help="Invoice address for current"
                                              "sales order.")
    partner_shipping_id = fields.Many2one('res.partner',
                                          string='Delivery Address',
                                          store=True,
                                          readonly=False, required=True,
                                          compute='_compute_partner_shipping_id',
                                          help="Delivery address for current"
                                               "sales order.")
    order_date = fields.Datetime(string='Date', readonly=True, index=True,
                                 copy=False, default=fields.Datetime.now,
                                 help="Date of order")
    laundry_person_id = fields.Many2one('res.users', string='Laundry Person',
                                        required=True,
                                        help="Name of laundry person")
    order_line_ids = fields.One2many('laundry.order.line', 'laundry_id',
                                     required=True, ondelete='cascade',
                                     help="Order lines of laundry orders")
    total_amount = fields.Float(compute='_compute_total_amount', string='Total',
                                store=True,
                                help="To get the Total amount")
    currency_id = fields.Many2one("res.currency", string="Currency",
                                  help="Name of currency")
    note = fields.Text(string='Terms and conditions',
                       help='Add terms and conditions')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('order', 'Laundry Order'),
        ('process', 'Processing'),
        ('done', 'Done'),
        ('return', 'Returned'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True,
        track_visibility='onchange', default='draft', help="State of the Order")

    @api.model_create_multi
    def create(self, vals_list):
        """Creating the record of Laundry order."""
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('laundry.order')
        return super().create(vals_list)

    @api.depends('order_line_ids')
    def _compute_total_amount(self):
        """Computing the total of total_amount in order lines."""
        total = 0
        for order in self:
            for line in order.order_line_ids:
                total += line.amount
            order.total_amount = total

    def confirm_order(self):
        """Confirming the order and after confirming order,it will create the
             washing model"""
        self.state = 'order'
        product_id = self.env.ref(
            'laundry_management.product_product_laundry_service')
        self.sale_id = self.env['sale.order'].create(
            {'partner_id': self.partner_id.id,
             'partner_invoice_id': self.partner_invoice_id.id,
             'partner_shipping_id': self.partner_shipping_id.id,
             'user_id': self.laundry_person_id.id,
             'order_line': [Command.create({'product_id': product_id.id,
                                            'name': 'Laundry Service',
                                            'price_unit': self.total_amount,
                                            })]
             })
        for order in self:
            for line in order.order_line_ids:
                self.env['washing.washing'].create(
                    {'name': line.product_id.name + '-Washing',
                     'user_id': line.washing_type_id.assigned_person_id.id,
                     'description': line.description,
                     'laundry_id': line.id,
                     'state': 'draft',
                     'washing_date': datetime.now().strftime(
                         '%Y-%m-%d %H:%M:%S')})

    def action_create_invoice(self):
        """Creating a new invoice for the laundry orders."""
        if self.sale_id.state in ['draft', 'sent']:
            self.sale_id.action_confirm()
        self.invoice_status = self.sale_id.invoice_status
        return {
            'name': 'Create Invoice',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.advance.payment.inv',
            'type': 'ir.actions.act_window',
            'context': {'laundry_sale_id': self.sale_id.id},
            'target': 'new'
        }

    def action_return_dress(self):
        """Return dress after laundry"""
        self.state = 'return'

    def action_cancel_order(self):
        """Cancel the laundry order with proper validation."""
        for record in self:
            record.state = 'cancel'

    def _compute_invoice_count(self):
        """Compute the invoice count."""
        for order in self:
            order.invoice_count = len(order.env['account.move'].search(
                [('invoice_origin', '=', order.sale_id.name)]))

    def _compute_work_count(self):
        """Computing the work count"""
        if self.id:
            wrk_ordr_ids = self.env['washing.washing'].search(
                [('laundry_id.laundry_id.id', '=', self.id)])
            self.work_count = len(wrk_ordr_ids)
        else:
            self.work_count = False

    def action_view_laundry_works(self):
        """Function for viewing the laundry works."""
        work_obj = self.env['washing.washing'].search(
            [('laundry_id.laundry_id.id', '=', self.id)])
        work_ids = []
        for each in work_obj:
            work_ids.append(each.id)
        view_id = self.env.ref('laundry_management.washing_washing_view_form').id
        if work_ids:
            if len(work_ids) <= 1:
                value = {
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'washing.washing',
                    'view_id': view_id,
                    'type': 'ir.actions.act_window',
                    'name': _('Works'),
                    'res_id': work_ids and work_ids[0]
                }
            else:
                value = {
                    'domain': str([('id', 'in', work_ids)]),
                    'view_type': 'form',
                    'view_mode': 'list,form',
                    'res_model': 'washing.washing',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'name': _('Works'),
                }
            return value

    def action_view_invoice(self):
        """Function for viewing Laundry orders invoices."""
        self.ensure_one()
        inv_ids = []
        for each in self.env['account.move'].search(
                [('invoice_origin', '=', self.sale_id.name)]):
            inv_ids.append(each.id)
        if inv_ids:
            if len(inv_ids) <= 1:
                value = {
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'account.move',
                    'view_id': self.env.ref('account.view_move_form').id,
                    'type': 'ir.actions.act_window',
                    'name': _('Invoice'),
                    'res_id': inv_ids and inv_ids[0]
                }
            else:
                value = {
                    'domain': str([('id', 'in', inv_ids)]),
                    'view_type': 'form',
                    'view_mode': 'list,form',
                    'res_model': 'account.move',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'name': _('Invoice'),
                }
            return value

    def unlink(self):
        """Delete the current record (Admin only)."""
        if not self.env.user.has_group('laundry_management.group_laundry_admin'):
            raise ValidationError("Only Laundry Admin can delete orders.")

        for record in self:
            if record.state not in ['draft', 'order']:
                raise ValidationError("You can only delete Draft or Confirmed orders.")

        return super().unlink()

    @api.depends('partner_id')
    def _compute_partner_shipping_id(self):
        for order in self:
            order.partner_shipping_id = order.partner_id.address_get(['delivery'])[
                'delivery'] if order.partner_id else False

    @api.depends('partner_id')
    def _compute_partner_invoice_id(self):
        for order in self:
            order.partner_invoice_id = order.partner_id.address_get(['invoice'])['invoice'] if order.partner_id else False

class LaundryOrderLine(models.Model):
    """Laundry order lines generating model"""
    _name = 'laundry.order.line'
    _description = "Laundry Order Line"

    product_id = fields.Many2one('product.product', string='Dress',
                                 required=True, help="Name of the product")
    qty = fields.Integer(string='No of items', required=True,
                         help="Number of quantity")
    description = fields.Text(string='Description',
                              help='Description of the line.')
    washing_type_id = fields.Many2one('washing.type', string='Washing Type',
                                      required=True,
                                      help='Select the type of wash')
    extra_work_ids = fields.Many2many('washing.work', string='Extra Work',
                                      help='Add if any extra works')
    amount = fields.Float(compute='_compute_amount', string='Amount',
                          help='Total amount of the line.')
    laundry_id = fields.Many2one('laundry.order', string='Laundry Order',
                                 help='Corresponding laundry order')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('wash', 'Washing'),
        ('extra_work', 'Make Over'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status of the line', readonly=True, copy=False, index=True,
        default='draft')

    @api.depends('washing_type_id', 'extra_work_ids', 'qty')
    def _compute_amount(self):
        """Compute the total amount"""
        for line in self:
            total = line.washing_type_id.amount * line.qty
            for each in line.extra_work_ids:
                total += each.amount * line.qty
            line.amount = total
