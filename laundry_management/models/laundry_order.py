# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sadique Kottekkat(odoo@cybrosys.com)
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
from odoo import models, fields, api, _
from datetime import datetime


class LaundryManagement(models.Model):
    """laundry orders generating model"""
    _name = 'laundry.order'
    _inherit = 'mail.thread'
    _description = "Laundry Order"
    _order = 'order_date desc, id desc'

    @api.model
    def create(self, vals):
        """
            Creating the record of laundry order.
        """
        vals['name'] = self.env['ir.sequence'].next_by_code('laundry.order')
        return super(LaundryManagement, self).create(vals)

    @api.depends('order_lines')
    def get_total(self):
        """
           Computing the total of total_amount in orderlines.
        """
        total = 0
        for obj in self:
            for each in obj.order_lines:
                total += each.amount
            obj.total_amount = total

    def confirm_order(self):
        """
            Confirming the order and after confirming order,it will create the
             washing.washing model.
        """
        self.state = 'order'
        sale_obj = self.env['sale.order'].create(
            {'partner_id': self.partner_id.id,
             'partner_invoice_id': self.partner_invoice_id.id,
             'partner_shipping_id': self.partner_shipping_id.id})
        self.sale_obj = sale_obj
        product_id = self.env.ref('laundry_management.laundry_service')
        self.env['sale.order.line'].create({'product_id': product_id.id,
                                            'name': 'Laundry Service',
                                            'price_unit': self.total_amount,
                                            'order_id': sale_obj.id
                                            })
        for each in self:
            for obj in each.order_lines:
                self.env['washing.washing'].create(
                    {'name': obj.product_id.name + '-Washing',
                     'user_id': obj.washing_type.assigned_person.id,
                     'description': obj.description,
                     'laundry_obj': obj.id,
                     'state': 'draft',
                     'washing_date': datetime.now().strftime(
                         '%Y-%m-%d %H:%M:%S')})

    def create_invoice(self):
        """
            Creating an new invoice for the laundry orders.
        """
        if self.sale_obj.state in ['draft', 'sent']:
            self.sale_obj.action_confirm()
        self.invoice_status = self.sale_obj.invoice_status
        return {
            'name': 'Create Invoice',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.advance.payment.inv',
            'type': 'ir.actions.act_window',
            'context': {'laundry_sale_obj': self.sale_obj.id},
            'target': 'new'
        }

    def return_dress(self):
        self.state = 'return'

    def cancel_order(self):
        self.state = 'cancel'

    def _invoice_count(self):
        wrk_ordr_ids = self.env['account.move'].search(
            [('invoice_origin', '=', self.sale_obj.name)])
        self.invoice_count = len(wrk_ordr_ids)

    def _work_count(self):
        if self.id:
            wrk_ordr_ids = self.env['washing.washing'].search(
                [('laundry_obj.laundry_obj.id', '=', self.id)])
            self.work_count = len(wrk_ordr_ids)
        else:
            self.work_count = False

    def action_view_laundry_works(self):
        """
            Function for viewing the laundry works.
        """
        work_obj = self.env['washing.washing'].search(
            [('laundry_obj.laundry_obj.id', '=', self.id)])
        work_ids = []
        for each in work_obj:
            work_ids.append(each.id)
        view_id = self.env.ref('laundry_management.washing_form_view').id
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
                    'view_mode': 'tree,form',
                    'res_model': 'washing.washing',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'name': _('Works'),
                    # 'res_id': work_ids
                }
            return value

    def action_view_invoice(self):
        """
            Function for viewing the invoices of laundry orders.
        """
        self.ensure_one()
        inv_obj = self.env['account.move'].search(
            [('invoice_origin', '=', self.sale_obj.name)])
        inv_ids = []
        for each in inv_obj:
            inv_ids.append(each.id)
        view_id = self.env.ref('account.view_move_form').id
        if inv_ids:
            if len(inv_ids) <= 1:
                value = {
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'account.move',
                    'view_id': view_id,
                    'type': 'ir.actions.act_window',
                    'name': _('Invoice'),
                    'res_id': inv_ids and inv_ids[0]
                }
            else:
                value = {
                    'domain': str([('id', 'in', inv_ids)]),
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'account.move',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'name': _('Invoice'),
                    # 'res_id': inv_ids
                }
            return value

    name = fields.Char(string="Label", copy=False)
    invoice_status = fields.Selection([
        ('upselling', 'Upselling Opportunity'),
        ('invoiced', 'Fully Invoiced'),
        ('to invoice', 'To Invoice'),
        ('no', 'Nothing to Invoice')
    ], string='Invoice Status', invisible=1, related='sale_obj.invoice_status',
        store=True, help="status of invoice")
    sale_obj = fields.Many2one('sale.order', invisible=1,
                               help="sequence name of sale order")
    invoice_count = fields.Integer(compute='_invoice_count',
                                   string='# Invoice',
                                   help="number of invoice count")
    work_count = fields.Integer(compute='_work_count', string='# Works',
                                help="number of work count")
    partner_id = fields.Many2one('res.partner', string='Customer',
                                 readonly=True,
                                 states={'draft': [('readonly', False)],
                                         'order': [('readonly', False)]},
                                 required=True,
                                 change_default=True, index=True,
                                 help="name of customer"
                                 )
    partner_invoice_id = fields.Many2one('res.partner',
                                         string='Invoice Address',
                                         readonly=True, required=True,
                                         states={
                                             'draft': [('readonly', False)],
                                             'order': [('readonly', False)]},
                                         help="Invoice address for current"
                                              " sales order.")
    partner_shipping_id = fields.Many2one('res.partner',
                                          string='Delivery Address',
                                          readonly=True, required=True,
                                          states={
                                              'draft': [('readonly', False)],
                                              'order': [('readonly', False)]},
                                          help="Delivery address for current"
                                               " sales order.")
    order_date = fields.Datetime(string='Date', readonly=True, index=True,
                                 states={'draft': [('readonly', False)],
                                         'order': [('readonly', False)]},
                                 copy=False, default=fields.Datetime.now,
                                 help="date of order")
    laundry_person = fields.Many2one('res.users', string='Laundry Person',
                                     required=1, help="name of laundry person")
    order_lines = fields.One2many('laundry.order.line', 'laundry_obj',
                                  required=1, ondelete='cascade',
                                  help="orderlines of laundry orders")
    total_amount = fields.Float(compute='get_total', string='Total', store=1,
                                help="total amount")
    currency_id = fields.Many2one("res.currency", string="Currency",
                                  help="name of currency")
    note = fields.Text(string='Terms and conditions')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('order', 'Laundry Order'),
        ('process', 'Processing'),
        ('done', 'Done'),
        ('return', 'Returned'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True,
        track_visibility='onchange', default='draft', help="state of the order")


class LaundryManagementLine(models.Model):
    """laundry orderlines generating model"""
    _name = 'laundry.order.line'
    _description = "Laundry Order Line"

    @api.depends('washing_type', 'extra_work', 'qty')
    def get_amount(self):
        for obj in self:
            total = obj.washing_type.amount * obj.qty
            for each in obj.extra_work:
                total += each.amount * obj.qty
            obj.amount = total

    product_id = fields.Many2one('product.product', string='Dress',
                                 required=1, help="name of the product")
    qty = fields.Integer(string='No of items', required=1,
                         help="number of quantity")
    description = fields.Text(string='Description')
    washing_type = fields.Many2one('washing.type', string='Washing Type',
                                   required=1)
    extra_work = fields.Many2many('washing.work', string='Extra Work')
    amount = fields.Float(compute='get_amount', string='Amount')
    laundry_obj = fields.Many2one('laundry.order', invisible=1)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('wash', 'Washing'),
        ('extra_work', 'Make Over'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, default='draft')
