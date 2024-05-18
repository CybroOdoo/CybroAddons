# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Raneesha M K (odoo@cybrosys.com)
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
import datetime
from odoo import api, fields, models


class BookOrder(models.Model):
    """
       Model for managing booked orders in the POS system.
    """
    _name = 'book.order'
    _description = "Point of Sale Booked Orders"

    name = fields.Char(string='Booking Ref', readonly=True,
                       help="Order reference of book order", copy=False,
                       default='/')
    company_id = fields.Many2one('res.company', string='Company',
                                 readonly=True, help="Current company",
                                 default=lambda self: self.env.user.company_id)
    date_quotation = fields.Datetime(string='Quotation Date',
                                     help="Quotation crated date",
                                     readonly=True, default=fields.Datetime.now)
    date_order = fields.Date(string='Order Date', help="Ordered date",
                             readonly=True, index=True,
                             default=fields.Date.today())
    amount_tax = fields.Float(compute='_compute_amount_all', string='Taxes',
                              digits=0, default=1.2,
                              help="Total amount of order with tax")
    amount_total = fields.Float(compute='_compute_amount_all', string='Total',
                                digits=0, help="Total amount of order")
    book_line_ids = fields.One2many('book.order.line', 'order_id',
                                    string='Order Lines',
                                    help="Order line of booked orders",
                                    copy=True)
    partner_id = fields.Many2one('res.partner', string='Customer',
                                 help="Whose we try to create order",
                                 change_default=True, index=True)
    state = fields.Selection([('draft', 'New'), ('confirmed', 'Confirmed')],
                             string="Status",
                             readonly=True, default='draft',
                             help="Stages of booked order")
    note = fields.Text(string='Internal Notes',
                       help="Description about book order")
    fiscal_position_id = fields.Many2one('account.fiscal.position',
                                         help="Fiscal position account "
                                              "for order",
                                         string='Fiscal Position')
    pickup_date = fields.Datetime(string='Pickup Date', readonly=True,
                                  help="Pickup date of the booked order")
    deliver_date = fields.Datetime(string='Deliver Date', readonly=True,
                                   help="Delivery date of the booked order")
    phone = fields.Char(string="Contact no",
                        help='Phone of customer for delivery')
    delivery_address = fields.Char(string="Delivery Address",
                                   help='Address of customer for delivery')
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist',
                                   help="Pricelist of order from session")
    pos_order_uid = fields.Char(help="Related Pos order",
                                string='Related Pos order')
    @api.model
    def _amount_line_tax(self, line, fiscal_position_id):
        """ Calculates the tax amount of the order line"""
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

    @api.depends('book_line_ids.price_subtotal_incl', 'book_line_ids.discount')
    def _compute_amount_all(self):
        """ To compute total amount with tax and without tax """
        for order in self:
            order.amount_tax = 0.0
            currency = order.pricelist_id.currency_id
            order.amount_tax = currency.round(
                sum(self._amount_line_tax(line, order.fiscal_position_id) for
                    line in order.book_line_ids))
            amount_untaxed = currency.round(
                sum(line.price_subtotal for line in order.book_line_ids))
            order.amount_total = order.amount_tax + amount_untaxed

    def action_confirm(self):
        """ Function to confirm the book order"""
        self.write({
            'state': 'confirmed',
        })
        return self.pos_order_uid

    @api.model
    def create(self, vals):
        """ Inherited create function to generate sequence number
            for booker orders
            :return record: created record
        """
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'book.order') or '/'
        return super(BookOrder, self).create(vals)

    @api.model
    def create_booked_order(self, partner, phone, address, date, price_list,
                            product, note, pickup, delivery, pos_order_uid):
        """ It creates a booked order based on the value in the booking popup
             in PoS ui.
             partner(int): id of partner
             phone(string): contact number of customer
             address(string): contact address of the customer
             date(date): ordered date
             price_list(int): price list id of order
             product(dict): dictionary values with product ids and  quantity
             note(string): Order note
             pickup(date): pickup date of the booked order
             delivery(date): delivery date of the booked order
        """
        book_date = (datetime.datetime.fromisoformat(date[:-1])).strftime(
            '%Y-%m-%d %H:%M:%S')
        order = self.create({
            'partner_id': partner,
            'phone': phone,
            'delivery_address': address,
            'pricelist_id': price_list,
            'date_quotation': book_date,
            'pos_order_uid': pos_order_uid,
            'book_line_ids': [(0, 0, {
                'product_id': product['product_id'][i],
                'qty': product['qty'][i],
                'price_unit': product['price'][i],
            }) for i in range(len(product['product_id']))],
            'note': note,
        })
        if pickup:
            order.write({'pickup_date': pickup + ' 00:00:00'})
        if delivery:
            order.write({'deliver_date': delivery + ' 00:00:00'})
        return order.name

    @api.model
    def all_orders(self):
        """To fetch all draft stage orders to PoS Booked orders screen
             dict: returns dictionary of values with orders details
        """
        values = []
        for rec in self.search([('state', '=', 'draft')]):
            products = []
            for line in rec.book_line_ids:
                products.append({
                    'id': line.product_id.id,
                    'qty': line.qty,
                    'price': line.price_unit
                })
            values.append({'id': rec.id,
                           'name': rec.name,
                           'partner_id': rec.partner_id.id,
                           'partner_name': rec.partner_id.name,
                           'address': rec.delivery_address,
                           'note': rec.note,
                           'phone': rec.phone,
                           'date': rec.date_quotation,
                           'pickup': rec.pickup_date,
                           'deliver': rec.deliver_date,
                           'products': products,
                           'total': rec.amount_total
                           })
        return values
