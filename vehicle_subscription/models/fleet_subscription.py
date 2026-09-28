# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Abhijith CK(<https://www.cybrosys.com>)
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
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = 'vehicle_id'

    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle",
                                 domain="[('id', 'in',vehicle_ids)]",
                                 help="This field help you to choose vehicle",
                                 required=True, tracking=True)
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
                                  help="Compute field which results the price"
                                       "of vehicle until the date ")
    extra_price = fields.Float(string="Extra Price",
                               compute="_compute_extra_price",
                               help="Compute field which results the extra "
                                    "price of vehicle")
    start_date = fields.Date(string="Start Date", required=True, tracking=True,
                             help="Start date of subscription")
    end_date = fields.Date(string="End Date", required=True, tracking=True,
                           help="End date of subscription")
    cancellation_date = fields.Date(string="Cancellation Date",
                                    default=fields.Date.today, tracking=True,
                                    help="Subscription cancellation date")
    duration = fields.Integer(string="Duration", compute='_compute_duration',
                              help="Compute subscription duration")
    cancel_duration = fields.Integer(string="Duration",
                                     compute='_compute_cancel_duration',
                                     help="compute cancel duration")
    state = fields.Selection(
        selection=[('draft', 'Draft'), ('subscribed', 'Subscribed'),
                   ('cancel', 'Cancelled'), ('expired', 'Expired')
                   ], string='State', default='draft', tracking=True,
        help="States of subscription")
    street = fields.Char(string="Street", help="Choose the street")
    state_id = fields.Many2one("res.country.state", string='State',
                               ondelete='restrict',
                               domain="[('country_id', '=?', country_id)]",
                               help="Choose the state")
    city = fields.Char(string="City", help="Choose the city")
    country_id = fields.Many2one('res.country', string='Country',
                                 ondelete='restrict',
                                 help="Choose the country")
    fuel = fields.Selection(selection=[('with_fuel', 'With Fuel'),
                                       ('without_fuel', 'Without Fuel')],
                            string="Fuel Choice", tracking=True,
                            help="Help you to choose the type of fuel")
    payment_type = fields.Selection(selection=[('full', 'Full Payment'),
                                               ('monthly', 'Monthly Payment')],
                                    string="Payment Type", default='full', tracking=True,
                                    help="Payment type opted during booking")
    fuel_type = fields.Selection(string="Fuel Type",
                                 related=
                                 "vehicle_id.model_id.default_fuel_type",
                                 help="Fuel type will be given which is related"
                                      " to the model")
    fuel_rate = fields.Integer(string="Rate", default=300, help="Rate of fuel")
    charge_km = fields.Integer(string="Charge in km", default=12,
                               help="Rate per kilometer")
    default_km = fields.Float(string="Default KMS",
                              related='vehicle_id.free_km',
                              help="Default km is set based on free km of "
                                   "vehicle which is given by authorised "
                                   "person")
    extra_km = fields.Float(string="Extra KMS", default=1,
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
                         ('state', '!=', 'subscribed')]):
                    domain.append(record.id)
        return domain

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------

    @api.depends('vehicle_id', 'seating_capacity')
    def _compute_vehicle_ids(self):
        """Compute the vehicle_IDS based on the vehicle and seating
        capacity."""
        for rec in self:
            domain = rec._get_vehicle_domain()
            if rec.seating_capacity:
                model_id = self.env['fleet.vehicle'].search(
                    [('state_id', '=', 'registered'),
                     ('model_id.seats', '=', rec.seating_capacity),
                     ('id', 'in', domain)])
            else:
                model_id = self.env['fleet.vehicle'].search(
                    [('id', 'in', domain)])

            if rec.vehicle_id:
                model_id |= rec.vehicle_id

            rec.vehicle_ids = model_id

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
                days = (record.cancellation_date - record.start_date).days
                record.cancel_duration = max(days, 0)
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
                rec.extra_price = (
                        (rec.extra_km / rec.mileage) * rec.fuel_rate)

    @api.depends('duration', 'insurance_type_id', 'vehicle_id.subscription_price')
    def _compute_price(self):
        """Function used to compute price of vehicle including per-day pro-rated insurance"""
        for rec in self:
            insurance_per_day = rec.insurance_type_id.insurance_amount_per_day if rec.insurance_type_id else 0.0
            rec.price = rec.duration * (rec.vehicle_id.subscription_price + insurance_per_day)

    @api.depends('cancel_duration', 'cancellation_date', 'start_date', 'duration', 'sale_id')
    def _compute_uptodate_price(self):
        """Compute price as per the cancellation date"""
        for rec in self:
            if rec.duration and rec.start_date and rec.cancellation_date and rec.sale_id and rec.sale_id.order_line:
                price_unit = rec.sale_id.order_line[0].price_unit
                days_used = (rec.cancellation_date - rec.start_date).days
                if days_used <= 0:
                    rec.uptodate_price = 0.0
                elif days_used >= rec.duration:
                    rec.uptodate_price = price_unit
                else:
                    rec.uptodate_price = round((price_unit / rec.duration) * days_used, 2)
            else:
                rec.uptodate_price = 0.0

    def _compute_sale(self):
        """Used to calculate the sale count"""
        for record in self:
            record.sale = self.env['sale.order'].search_count(
                [('id', 'in', self.sale_id.ids)])

    def _compute_refund(self):
        """Used to calculate count of refund"""
        for record in self:
            record.refund = self.env['account.move'].search_count(
                [('id', '=', self.refund_id.id)])

    def _compute_invoice(self):
        """Used to calculate invoice count"""
        for record in self:
            invoice_ids = record.invoice_ids + record.sale_id.invoice_ids
            record.invoice = self.env['account.move'].search_count(
                [('id', 'in', invoice_ids.ids)])

    # -------------------------------------------------------------------------
    # CONSTRAINS AND ONCHANGE METHODS
    # -------------------------------------------------------------------------

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """Ensure that the start date is not greater than the end date."""
        for rec in self:
            if rec.start_date > rec.end_date:
                raise ValidationError(
                    "Start Date cannot be greater than End Date")

    @api.onchange('vehicle_id')
    def _onchange_vehicle_id(self):
        """Function used to fill the seating capacity, fuel rate, and charge km from selected vehicle"""
        if self.vehicle_id:
            if not self.seating_capacity:
                self.seating_capacity = self.vehicle_id.model_id.seats
            self.fuel_rate = self.vehicle_id.fuel_rate
            self.charge_km = self.vehicle_id.charge_km

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

    @api.onchange('end_date')
    def _onchange_end_date(self):
        """Check expiry for subscription"""
        if self.end_date and self.end_date < fields.Date.today():
            self.state = 'expired'

    # -------------------------------------------------------------------------
    # CRUD OVERRIDES
    # -------------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('vehicle_id'):
                vehicle = self.env['fleet.vehicle'].browse(vals['vehicle_id'])
                if vehicle.exists():
                    if 'fuel_rate' not in vals:
                        vals['fuel_rate'] = vehicle.fuel_rate
                    if 'charge_km' not in vals:
                        vals['charge_km'] = vehicle.charge_km
        return super().create(vals_list)

    # -------------------------------------------------------------------------
    # ACTION METHODS
    # -------------------------------------------------------------------------

    def action_get_car_insurance(self):
        """Get the action to view the car
        insurance associated with the subscription."""
        self.ensure_one()
        insurance = self.insurance_type_id
        if not insurance and self.vehicle_id:
            insurance = self.env['vehicle.insurance'].sudo().search(
                [('vehicle_id', '=', self.vehicle_id.id)], limit=1)
            if insurance:
                self.sudo().write({'insurance_type_id': insurance.id})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Insurance',
            'view_mode': 'form',
            'res_model': 'vehicle.insurance',
            'res_id': insurance.id if insurance else False,
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

    def action_get_invoice(self):
        """Get the action to view the invoice
        associated with the subscription."""
        invoice_ids = self.invoice_ids + self.sale_id.invoice_ids
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Order',
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'domain': [('id', 'in', invoice_ids.ids)],
            'context': [('create', '=', False)]
        }

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
            [('product_tmpl_id', '=', product_template_id)], limit=1)
        all_invoices = self.env['account.move'].search(
            [('id', 'in', (self.invoice_ids | self.sale_id.invoice_ids).ids)])
        paid_invoices = all_invoices.filtered(lambda inv: inv.payment_state in ['paid', 'in_payment', 'partial'])
        invoiced_amount = sum(paid_invoices.mapped('amount_untaxed_signed'))
        total_price = self.uptodate_price + self.extra_price
        if invoiced_amount == total_price or invoiced_amount <= total_price:
            self.write({'state': 'cancel'})
            if self.sale_id:
                self.sale_id.action_lock()
        elif invoiced_amount > total_price:
            self.write({'state': 'cancel'})
            if not self.refund_id:
                refund_amount = round(invoiced_amount - total_price, 2)
                if refund_amount > 0:
                    self.refund_id = self.env['account.move'].create({
                        'move_type': 'out_refund',
                        'invoice_date': fields.Date.today(),
                        'partner_id': self.customer_id.id,
                        'invoice_line_ids': [fields.Command.create({
                            'product_id': product_id.id,
                            'name': self.vehicle_id.name,
                            'price_unit': refund_amount,
                        })]
                    })
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Warning'),
                    'message': _(
                        'You need to pay the amount till date in order to '
                        'cancel the subscription'),
                    'sticky': True,
                }
            }

    # -------------------------------------------------------------------------
    # BUSINESS & CRON METHODS
    # -------------------------------------------------------------------------

    @api.model
    def _cron_check_subscription_expiry(self):
        """Cron method to expire subscriptions past their end date."""
        today = fields.Date.today()
        expired_subs = self.search([
            ('state', '=', 'subscribed'),
            ('end_date', '<', today)
        ])
        expired_subs.write({'state': 'expired'})
