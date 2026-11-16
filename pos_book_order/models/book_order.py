# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import api, fields, models
from odoo.fields import Command


class BookOrder(models.Model):
    """
       Model for managing booked orders in the POS system.
    """
    _name = 'book.order'
    _description = "Point of Sale Booked Orders"

    name = fields.Char(string='Booking Ref', readonly=True,
                       help="Name of the booked order",
                       copy=False, default='/')
    company_id = fields.Many2one('res.company',
                                 help="Company of the booked order",
                                 default=lambda self: self.env.company)
    date_quotation = fields.Datetime(string='Quotation Date',
                                     help="Quotation created date",
                                     readonly=True, index=True,
                                     default=fields.Datetime.now)
    date_order = fields.Date(string='Order Date', help="Order created date",
                             readonly=True, index=True,
                             default=fields.Date.context_today)
    amount_tax = fields.Float(compute='_compute_amount_all', string='Taxes',
                              help="Tax amount for the order",
                              digits=0)
    amount_total = fields.Float(compute='_compute_amount_all', string='Total',
                                help="Total amount of the order",
                                digits=0)
    book_line_ids = fields.One2many('book.order.line',
                                    'order_id',
                                    help="Order Line of book orders",
                                    string='Order Lines',
                                    copy=True)
    partner_id = fields.Many2one('res.partner', string='Customer',
                                 help="Partner of the order",
                                 change_default=True, index=True)
    state = fields.Selection([('draft', 'New'),
                              ('confirmed', 'Confirmed')],
                             string='Status', readonly=True, copy=False,
                             help="Current status of the order",
                             default='draft')
    note = fields.Text(string='Internal Notes',
                       help="Enter any notes regarding order")
    fiscal_position_id = fields.Many2one('account.fiscal.position',
                                         help="Fiscal position account "
                                              "for order")
    pos_order_uid = fields.Char(help="Related Pos order",
                                string='Related Pos Order')
    pickup_date = fields.Datetime(readonly=True,
                                  help="Picking date of the order")
    deliver_date = fields.Datetime(readonly=True,
                                   help="Delivering date of the order")
    phone = fields.Char('Contact No', help='Phone of customer for delivery')
    delivery_address = fields.Char(help='Address of customer for delivery')
    pricelist_id = fields.Many2one('product.pricelist',
                                   help="Pricelist of the order")

    @api.model
    def _amount_line_tax(self, line, fiscal_position_id):
        """ Calculates the tax amount of the order line.
            :param line: Order line record
            :param fiscal_position_id: Fiscal position account for order
            :return float: Total tax amount as float
        """
        taxes = line.tax_ids.filtered(
            lambda t: t.company_id.id == line.order_id.company_id.id)
        taxes = fiscal_position_id.map_tax(taxes)
        price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
        taxes = taxes.compute_all(price,
                                  line.order_id.pricelist_id.currency_id,
                                  line.qty, product=line.product_id,
                                  partner=line.order_id.partner_id or False)[
            'taxes']
        return sum(tax.get('amount', 0.0) for tax in taxes)

    @api.depends('book_line_ids.price_subtotal_incl',
                 'book_line_ids.discount')
    def _compute_amount_all(self):
        """ To compute total amount with tax and without tax """
        for order in self:
            order.amount_tax = 0.0
            currency = self.env.company.currency_id
            order.amount_tax = currency.round(
                sum(self._amount_line_tax(line, order.fiscal_position_id) for
                    line in order.book_line_ids))
            amount_untaxed = currency.round(
                sum(line.price_subtotal for line in order.book_line_ids))
            order.amount_total = order.amount_tax + amount_untaxed


    @api.model_create_multi
    def create(self, vals_list):
        """ Inherited create function to generate sequence number
            for booked orders
            :return record: created record
        """
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'book.order') or '/'
        return super().create(vals_list)

    def action_confirm(self):
        """ Function to confirm the book order"""
        self.write({
            'state': 'confirmed',
        })
        return self.pos_order_uid if len(self) == 1 else self.mapped('pos_order_uid')


    @api.model
    def create_booked_order(self, partner, phone, address, date, price_list,
                            product, note, pickup_date, delivery_date, pos_order):
        """ It creates a booked order based on the value in the booking popup
             in PoS ui.
             partner(int): id of partner
             phone(string): contact number of customer
             address(string): contact address of the customer
             date(date): ordered date
             price_list(int): price list id of order
             product(dict): dictionary values with product ids and quantity
             note(string): Order note
             pickup_date(string): pickup date of the booked order
             delivery_date(string): delivery date of the booked order
             pos_order(string): POS order UID
        """
        order = self.create({
            'partner_id': partner,
            'phone': phone,
            'delivery_address': address,
            'pricelist_id': price_list if price_list else False,
            'date_quotation': fields.Date.context_today(self) if not date else date,
            'pos_order_uid': pos_order,
            'book_line_ids': [Command.create({
                'product_id': product['product_id'][i],
                'qty': product['qty'][i],
                'price_unit': float(product['price'][i]),
                'tax_ids': [Command.set(product['tax_ids'][i])],
            }) for i in range(len(product['product_id']))],
            'note': note,
        })
        if pickup_date:
            order.write({'pickup_date': pickup_date + ' 00:00:00' if ' ' not in str(pickup_date) else pickup_date})
        if delivery_date:
            order.write({'deliver_date': delivery_date + ' 00:00:00' if ' ' not in str(delivery_date) else delivery_date})
        return {
            'id': order.id,
            'name': order.name,
        }

    @api.model
    def all_orders(self, state=None, limit=200):
        """ To fetch booked orders to PoS Booked orders screen
            :param state: Optional filter ('draft', 'confirmed', or 'all')
            :param limit: Maximum number of records to return (default: 200)
            :return list: A list of dictionaries containing information
                        about each order
        """
        values = []
        domain = ['|', ('company_id', '=', False), ('company_id', '=', self.env.company.id)]
        if state and state in ('draft', 'confirmed'):
            domain.append(('state', '=', state))
        for rec in self.search(domain, order='state asc, date_quotation desc, id desc', limit=limit):
            products = [
                {
                    'id': line.product_id.id,
                    'qty': line.qty,
                    'price': line.price_unit,
                }
                for line in rec.book_line_ids
            ]
            values.append({
                'id': rec.id,
                'name': rec.name,
                'state': rec.state,
                'partner_id': rec.partner_id.id,
                'partner_name': rec.partner_id.name,
                'address': rec.delivery_address,
                'note': rec.note,
                'phone': rec.phone,
                'date': rec.date_quotation,
                'pickup': rec.pickup_date,
                'deliver': rec.deliver_date,
                'products': products,
                'total': rec.amount_total,
                'pos_order_uid': rec.pos_order_uid,
            })

        return values
