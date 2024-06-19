# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Rahna Rasheed (<https://www.cybrosys.com>)
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
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class VehicleSubscription(models.Model):
    """Created new model to add new fields and function"""
    _name = "fleet.subscription"
    _description = "Fleet Subscription"
    _inherit = "mail.thread"
    _rec_name = 'vehicle_id'

    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle",
                                 domain="[('id', 'in',vehicle_ids)]",
                                 help="This field help you to choose vehicle")
    vehicle_ids = fields.Many2many('fleet.vehicle', string="Vehicle",
                                   compute='_compute_vehicle_ids',
                                   help="Returns vehicle by satisfying "
                                        "the domain")
    model_id = fields.Many2one(related="vehicle_id.model_id", string='Model',
                               help="This field help you to choose model "
                                    "of vehicle")
    price = fields.Float(compute="_compute_price", string='Price',
                         help="Compute field which results the price of vehicle")
    uptodate_price = fields.Float(compute="_compute_uptodate_price",
                                  string='Price',
                                  help="Compute field which results the price "
                                       "of vehicle until the date ")
    extra_price = fields.Float(string="Extra Price",
                               compute="_compute_extra_price",
                               help="Compute field which results the extra "
                                    "price of vehicle")
    start_date = fields.Date(string="Start Date", required=True,
                             help="Start date of subscription")
    end_date = fields.Date(string="End Date", required=True,
                           help="End date of subscription")
    cancellation_date = fields.Date(string="Cancellation Date",
                                    default=fields.Date.today(),
                                    help="Subscription cancellation date")
    duration = fields.Integer(string="Duration", compute='_compute_duration',
                              help="Compute subscription duration")
    cancel_duration = fields.Integer(string="Duration",
                                     compute='_compute_cancel_duration',
                                     help="compute cancel duration")
    state = fields.Selection(
        selection=[('draft', 'Draft'), ('subscribed', 'Subscribed'),
                   ('cancel', 'Cancelled'), ('expired', 'Expired')
                   ], string='State', default='draft',
        help="States of subscription")
    street = fields.Char(string="Street", help="Choose the street")
    state_id = fields.Many2one("res.country.state", string='State',
                               ondelete='restrict',
                               domain="[('country_id', '=?', country_id)]",
                               help="Choose the state")
    city = fields.Char(string="City", help="Choose the city")
    country_id = fields.Many2one('res.country', string='Country',
                                 ondelete='restrict', help="Choose the country")
    fuel = fields.Selection(selection=[('with_fuel', 'With Fuel'),
                                       ('without_fuel', 'Without Fuel')],
                            string="Fuel Choice", default='without_fuel',
                            help="Help you to choose the type of fuel")
    fuel_type = fields.Selection(string="Fuel Type",
                                 related=
                                 "vehicle_id.model_id.default_fuel_type",
                                 help="Fuel type will be given which is related"
                                      " to the model")
    fuel_rate = fields.Integer(String="Rate", default=300, help="Rate of fuel")
    charge_km = fields.Integer(string="Charge in km", default=12,
                               help="Rate per kilometer")
    default_km = fields.Float(string="Default KMS",
                              related='vehicle_id.free_km',
                              help="Default km is set based on free km of "
                                   "vehicle which is given by authorised "
                                   "person")
    extra_km = fields.Float(string="Extra KMS", default_km=1,
                            help="As per customer he/she can choose extra km")
    mileage = fields.Float(string='Mileage',
                           related='vehicle_id.model_id.mileage',
                           help="Helps to set mileage of vehicle")
    sale = fields.Integer(string="sale", compute='_compute_sale',
                          help="Helps you to store count of sale")
    invoice = fields.Integer(string="Invoice", compute='_compute_invoice',
                             help="Helps you to store count of invoice")
    invoice_ids = fields.Many2many('account.move', string='Invoices',
                                   help="Used to store ids of invoices")
    customer_id = fields.Many2one('res.partner', string="Customer",
                                  help="Helps you to choose customer")
    sale_id = fields.Many2one('sale.order', string='sale', readonly=True,
                              help="Stores id of sale order")
    refund_id = fields.Many2one('account.move', string='Refund', readonly=True,
                                help="Stores id of invoice which belongs "
                                     "to refund")
    insurance_type_id = fields.Many2one('vehicle.insurance',
                                        domain=
                                        "[('vehicle_id', '=',vehicle_id)]")
    refund = fields.Integer(compute='_compute_refund',
                            help="Helps you to store count of refund")
    seating_capacity = fields.Integer(string='Seating Capacity',
                                      help="Seating capacity of vehicle can "
                                           "be set")
    invisible_sub = fields.Boolean(string="Approve Subscription",
                                   help="As subscription request get approved "
                                        "this field will be enabled")

    def _get_vehicle_domain(self):
        """This method retrieves the vehicles that meet the following
        criteria"""
        insurance_ids = self.env['vehicle.insurance'].search([]).mapped(
            'vehicle_id')
        domain = []
        for record in insurance_ids:
            state = record.log_services.mapped('state')
            if 'done' in state and 'running' not in state and 'new' \
                    not in state and 'cancelled' not in state:
                if not self.search(
                        [('vehicle_id', '=', record.id),
                         ('state', '!=', 'subscribe')]):
                    domain.append(record.id)
        return domain

    @api.onchange('vehicle_id')
    def _onchange_vehicle_id(self):
        """Function used to fill the seating capacity"""
        if self.vehicle_id:
            self.seating_capacity = self.vehicle_id.model_id.seats

    @api.onchange('seating_capacity')
    def _onchange_seating_capacity(self):
        """As the seating capacity changes vehicles are shown """
        if self.seating_capacity != self.vehicle_id.model_id.seats:
            self.vehicle_id = False

    @api.onchange('default_km')
    def _onchange_default_km(self):
        """Charge per km is set as onchange of default_km"""
        if self.default_km <= self.vehicle_id.free_km:
            self.charge_km = 0

    @api.depends('vehicle_id', 'seating_capacity')
    def _compute_vehicle_ids(self):
        """Compute the vehicle_IDS based on the vehicle and seating capacity."""
        for rec in self:
            if not rec.vehicle_ids:
                domain = rec._get_vehicle_domain()
                if rec.seating_capacity:
                    model_id = self.env['fleet.vehicle'].search(
                        [('state_id', '=', 'registered'),
                         ('model_id.seats', '=', rec.seating_capacity),
                         ('id', 'in', domain)])
                    for record in model_id:
                        self.vehicle_ids = [(4, record.id)]
                else:
                    model_id = self.env['fleet.vehicle'].search(
                        [('id', 'in', domain)])
                    for record in model_id:
                        self.vehicle_ids = [(4, record.id)]

    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        """Compute duration based on start and end date"""
        for record in self:
            if record.end_date:
                if record.end_date < record.start_date:
                    raise ValidationError(_(
                        "End date should be greater than start date."))
            if record.start_date and record.end_date:
                start = record.start_date.strftime("%Y-%m-%d")
                end = record.end_date.strftime("%Y-%m-%d")
                start_datetime = datetime.strptime(start, "%Y-%m-%d")
                end_datetime = datetime.strptime(end, "%Y-%m-%d")
                delta = end_datetime - start_datetime
                record.duration = delta.days
            else:
                record.duration = 0

    @api.depends('start_date', 'cancellation_date')
    def _compute_cancel_duration(self):
        """Compute duration based on cancellation date"""
        for record in self:
            if record.start_date and record.cancellation_date:
                start = record.start_date.strftime("%Y-%m-%d")
                end = record.cancellation_date.strftime("%Y-%m-%d")
                start_datetime = datetime.strptime(start, "%Y-%m-%d")
                end_datetime = datetime.strptime(end, "%Y-%m-%d")
                delta = end_datetime - start_datetime
                record.cancel_duration = delta.days
            else:
                record.cancel_duration = 0

    @api.depends('extra_km', 'charge_km', 'fuel_rate', 'fuel')
    def _compute_extra_price(self):
        """Compute extra charges based on criteria"""
        for rec in self:
            if rec.fuel == 'without_fuel':
                rec.extra_price = (rec.extra_km * rec.charge_km)
            elif rec.mileage == 0:
                raise ValidationError(_("Mileage cannot be zero."))
            else:
                rec.extra_price = ((rec.extra_km / rec.mileage) * rec.fuel_rate)

    @api.depends('duration')
    def _compute_price(self):
        """Function used to compute price of vehicle"""
        for rec in self:
            rec.price = (rec.duration * rec.vehicle_id.subscription_price) \
                        + rec.insurance_type_id.insurance_amount

    @api.depends('cancel_duration')
    def _compute_uptodate_price(self):
        """Compute price as per the cancellation date"""
        for rec in self:
            rec.uptodate_price = (
                    (rec.sale_id.order_line.price_unit / rec.duration) * (
                        (rec.cancellation_date - rec.start_date).days))

    def action_get_car_insurance(self):
        """Get the action to view the car
        insurance associated with the subscription."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Insurance',
            'view_mode': 'form',
            'res_model': 'vehicle.insurance',
            'res_id': self.insurance_type_id.id,
            'context': [('create', '=', False)]
        }

    def action_get_sale(self):
        """Get the action to view the sale
        associated with the subscription."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Order',
            'view_mode': 'form',
            'res_model': 'sale.order',
            'res_id': self.sale_id.id,
            'context': [('create', '=', False)]
        }

    def _compute_sale(self):
        """Used to calculate the sale count"""
        for record in self:
            record.sale = self.env['sale.order'].search_count(
                [('id', '=', self.sale_id.id)])

    def action_get_refund(self):
        """Get the action to view the refund
        associated with the subscription."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Refund',
            'view_mode': 'form',
            'res_id': self.refund_id.id,
            'res_model': 'account.move',
            'context': [('create', '=', False)]
        }

    def _compute_refund(self):
        """Used to calculate count of refund"""
        for record in self:
            record.refund = self.env['account.move'].search_count(
                [('id', '=', self.refund_id.id)])

    def action_get_invoice(self):
        """Get the action to view the invoice
        associated with the subscription."""
        invoice_ids = self.invoice_ids + self.sale_id.invoice_ids
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Order',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('id', 'in', invoice_ids.ids)],
            'context': [('create', '=', False)]
        }

    def _compute_invoice(self):
        """Used to calculate invoice count"""
        for record in self:
            invoice_ids = record.invoice_ids + record.sale_id.invoice_ids
            record.invoice = self.env['account.move'].search_count(
                [('id', 'in', invoice_ids.ids)])

    def action_invoice(self):
        """Used to generate invoice on clicking the button"""
        self.write({'state': 'subscribed'})
        product_template_id = self.env.ref(
            'vehicle_subscription.product_template_vehicle_subscription_form').id
        product_id = self.env['product.product'].search(
            [('product_tmpl_id', '=', product_template_id)])
        sale_order_id = self.env['sale.order'].create({
            'partner_id': self.customer_id.id,
            'order_line': [(0, 0, {
                'product_id': product_id.id,
                'name': self.vehicle_id.name,
                'price_unit': self.price + self.extra_price,
            })]
        })
        self.sale_id = sale_order_id

    def action_request(self):
        """Request for change subscription is generated """
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'change.subscription',
            'target': 'new',
        }

    def action_cancel(self):
        """Proceed with cancellation of subscription"""
        product_template_id = self.env.ref(
            'vehicle_subscription.product_template_vehicle_subscription_form').id
        product_id = self.env['product.product'].search(
            [('product_tmpl_id', '=', product_template_id)])
        invoice = self.env['account.move'].search(
            [('id', 'in', self.invoice_ids.ids),
             ('payment_state', 'in', ['paid', 'partial'])]).mapped(
            'amount_untaxed_signed')
        invoiced_amount = sum(invoice)
        total_price = self.uptodate_price
        if invoiced_amount == total_price:
            self.write({'state': 'cancel'})
            self.sale_id.action_done()
        elif invoiced_amount > total_price:
            self.write({'state': 'cancel'})
            self.refund_id = self.env['account.move'].create({
                'move_type': 'out_refund',
                'invoice_date': fields.Date.today(),
                'partner_id': self.customer_id.id,
                'invoice_line_ids': [(0, 0, {
                    'product_id': product_id.id,
                    'name': self.vehicle_id.name,
                    'price_unit': self.uptodate_price + self.extra_price,
                })]
            })
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Warning'),
                    'message': 'you need to pay amount till date inorder to '
                               'cancel subscription',
                    'sticky': True,
                }
            }

    @api.onchange('end_date')
    def _onchange_end_date(self):
        """Check expiry for subscription"""
        if self.end_date:
            if self.end_date < fields.Date.today():
                self.write({'state': 'expired'})
                self.sale_id.action_done()
