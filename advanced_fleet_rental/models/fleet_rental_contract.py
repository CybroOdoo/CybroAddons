# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anfas Faisal K (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from datetime import date
from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


class FleetRentalContract(models.Model):
    """
    Represents a car rental contract, including details about the customer,
    vehicle, rental period, charges, and various related information.
    """
    _name = 'fleet.rental.contract'
    _description = 'Fleet Rental Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Sequence",
                       default=lambda self: _('New'),
                       copy=False, readonly=True, tracking=True,
                       help='Unique contract number for the rental agreement.')

    state = fields.Selection(
        [('new', 'New'),
         ('in_progress', 'In Progress'),
         ('return', 'Return'), ('cancel', 'Cancel')],
        string='State', default='new',
        help='Contract Progress',
        group_expand='_group_expand_states',tracking=True)
    customer_id = fields.Many2one(
        'res.partner', string='Customer',
        help='The customer who is renting the vehicle.',
        required=True, tracking=True)
    email = fields.Char(string='Email',
                        related='customer_id.email',
                        help='Email address of the customer.',
                        readonly=False)
    phone = fields.Char('Phone', related='customer_id.phone',
                        help="Phone Number of the customer")
    pickup_date = fields.Datetime(
        string='Pick-up Date',
        help='Date and time when the vehicle will be picked up.',
        required=True, tracking=True)
    dropoff_date = fields.Datetime(
        string='Drop-off Date',
        help='Date and time when the vehicle will be returned.',
        required=True, tracking=True)
    pickup_location = fields.Char(
        string='Pick-Up Location',
        help='Location where the vehicle will be picked up.',
        required=True)
    dropoff_location = fields.Char(
        string='Drop-Off Location',
        help='Location where the vehicle will be dropped off.',
        required=True)
    pickup_street = fields.Char(
        string='Pick-Up Street',
        help='Street address for the pick-up location.',
        required=True)
    dropoff_street = fields.Char(
        string='Drop-Off Street',
        help='Street address for the drop-off location.',
        required=True)
    pickup_city = fields.Char(
        string='Pick-Up City',
        help='City where the vehicle will be picked up.',
        required=True)
    dropoff_city = fields.Char(
        string='Drop-Off City',
        help='City where the vehicle will be dropped off.',
        required=True)
    pickup_state_id = fields.Many2one(
        'res.country.state',
        string='Pick-Up State',
        help='State where the vehicle will be picked up.',
        required=True)
    dropoff_state_id = fields.Many2one(
        'res.country.state',
        string='Drop-Off State',
        help='State where the vehicle will be dropped off.',
        required=True)
    pickup_zip = fields.Char(
        string='Pick-Up ZIP',
        help='ZIP code for the pick-up location.',
        required=True)
    dropoff_zip = fields.Char(string='Drop-Off ZIP',
                              help='ZIP code for the drop-off location.')
    pickup_country_id = fields.Many2one(
        'res.country',
        string='Pick-Up Country',
        help='Country where the vehicle will be picked up.',
        required=True)
    dropoff_country_id = fields.Many2one(
        'res.country',
        string='Drop-Off Country',
        help='Country where the vehicle will be dropped off.',
        required=True)
    vehicle_id = fields.Many2one(
        'fleet.vehicle', string='Vehicle',
        help='The vehicle being rented.',
        required=True)
    model = fields.Char(related='vehicle_id.model_id.name', string='Model',
                        help='Model of the rented vehicle.')
    transmission = fields.Selection(
        [('automatic', 'Automatic'), ('manual', 'Manual')],
        string='Transmission', related='vehicle_id.transmission',
        help='Transmission type of the rented vehicle.')
    fuel_type = fields.Selection(
        [
            ('diesel', 'Diesel'),
            ('gasoline', 'Gasoline'),
            ('full_hybrid', 'Full Hybrid'),
            ('plug_in_hybrid_diesel', 'Plug-in Hybrid Diesel'),
            ('plug_in_hybrid_gasoline', 'Plug-in Hybrid Gasoline'),
            ('cng', 'CNG'),
            ('lpg', 'LPG'),
            ('hydrogen', 'Hydrogen'),
            ('electric', 'Electric'),
        ], string='Fuel Type', related='vehicle_id.fuel_type',
        help='Fuel type of the rented vehicle.')
    last_odometer = fields.Float(
        string='Last Odometer',
        related='vehicle_id.odometer',
        help='Last recorded odometer reading of the vehicle.')
    odometer_unit = fields.Selection(
        [('kilometers', 'km'), ('miles', 'mi')],
        string='Odometer Unit', default='kilometers',
        related='vehicle_id.odometer_unit',
        help='Unit of measurement for the odometer reading.')

    driver_required = fields.Boolean(
        string='Driver Required',
        help='Indicates if a driver is required for the rental.')
    driver_id = fields.Many2one(
        'res.partner', string='Driver',
        help='Driver assigned to the rental if required.')
    charge_type = fields.Selection(
        [('excluding', 'Excluding in rent charge'),
         ('including', 'Including in rent charge')],
        string='Charge Type',
        help='Specifies if the driver charge is included in the rental '
             'charge or not.')
    driver_charge = fields.Float(
        string='Driver Charge',
        help='Charge for the driver if not included '
             'in the rental charge.')

    # Rent Details
    rent_type = fields.Selection(
        [('hours', 'Hours'), ('days', 'Days'),
         ('kilometers', 'Kilometers')],
        string='Rent Type',
        default='hours',
        help='Type of rent calculation (per day, per kilometer, or per mile).')
    rent_per_hour = fields.Float(string='Rent / Hour',
                                 help='Rental charge per hour.',
                                 related='vehicle_id.rent_hour')
    total_hours = fields.Float(string='Total Hours ',
                               help="Total Hours Taken for Rent",
                               compute='_compute_rental_period', store=True,
                               readonly=False)
    rent_per_day = fields.Float(string='Rent / Day',
                                help='Rental charge per day.',
                                related='vehicle_id.rent_day')
    total_days = fields.Integer(string='Total Days',
                                help='Total number of rental days.',
                                compute='_compute_rental_period', store=True,
                                readonly=False)
    rent_per_km = fields.Float(string='Rent / KM',
                               help='Rental charge per km.'
                               , related='vehicle_id.rent_kilometer')
    total_km = fields.Integer(string='Total KM',
                              help='Total Kilometers.')
    total_rental_charge = fields.Float(
        string='Total Rental Charge',
        compute='_compute_total_rental_charge', store=True,
        help='Total rental charge for the contract.')

    payment_type = fields.Selection(
        [('daily', 'Daily'), ('weekly', 'Weekly'),
         ('monthly', 'Monthly'),
         ('full', 'Fully')],
        string='Payment Type',
        help='Payment schedule for the rental charge.',
        default='full')
    invoice_item_id = fields.Many2one(
        'product.product',
        string='Invoice Item',
        help='Description of the item to be invoiced.',
        default=lambda self: self.env.ref(
            'advanced_fleet_rental.product_product_vehicle_rental_charge'))
    is_extra_charge = fields.Boolean(string='Is any extra charge',
                                     help='Indicates if there are any extra '
                                          'charges applicable.')
    extra_per_hour = fields.Float(string='Extra Charges / Hour',
                                  help='Rental charge per hour.',
                                  related='vehicle_id.charge_hour')
    total_extra_hours = fields.Integer(string='Total Extra Hours',
                                       help='Total number of rental hours.')
    extra_per_day = fields.Float(string='Extra Charges / Day',
                                 help='Rental charge per hour.',
                                 related='vehicle_id.charge_day')
    total_extra_days = fields.Integer(string='Total Extra Days',
                                      help='Total number of rental days.')
    extra_per_km = fields.Float(string='Extra Charges / KM',
                                help='Rental charge per hour.',
                                related='vehicle_id.charge_kilometer')

    total_extra_km = fields.Float(string='Total Extra K/M',
                                  help="Total Extra K/M taken")
    total_extra_charge = fields.Float(string="Total Extra Charge",
                                      help="Extra Charges per K/M",
                                      compute='_compute_total_extra_charge'
                                      , store=True)

    rental_payment_plan_ids = (fields.One2many
                               ('rental.payment.plan',
                                'contract_id',
                                string="Vehicle Payment Details",
                                help="Details of the paymentplans for the"
                                     " vehicle rental."))
    extra_service_ids = (fields.One2many
                         ('extra.service',
                          'contract_id',
                          string="Extra Services",
                          help="List of extra services associated with this"
                               "vehicle rental."
                          ))
    is_extra_invoice_created = fields.Boolean(
        string='Extra Invoice Created',
        help="Indicates whether an extra invoice has been created for the"
             " extra services.")
    image_ids = fields.One2many(
        'multi.image',
        'contract_id',
        string="Images of the Vehicle",
        help="Images related to the Vehicles of vehicle rental."
    )
    insurance_ids = fields.One2many(
        'insurance.policy',
        'contract_id',
        string="Insurance Policy",
        help="Insurance policies associated with the vehicle rental.")

    vehicle_to_invoice_count = fields.Integer(
        string='Number of vehicle rent to invoice',
        compute='_compute_vehicle_to_invoice',
        readonly=True,
        help="Number of vehicle rental invoices that is created."
    )
    is_damaged_invoiced = fields.Boolean(
        string='Damage Invoice Created',
        help="Indicates whether an extra invoice has been created for the"
             " extra services.")
    cancellation_policy_id = fields.Many2one(
        'cancellation.policy', string='Cancellation Policy',
        help='Select the cancellation policy applicable for this record. '
             'The cancellation charges will be calculated based on the '
             'selected policy.')
    cancellation_charge = fields.Float(string='Cancellation Charge')

    cancellation_terms = fields.Text(
        string='Cancellation Terms and Conditions',
        related="cancellation_policy_id.terms_conditions",
        readonly=False)
    is_cancelled_invoiced = fields.Boolean(
        string='Cancelled Invoice Created',
        help="Indicates whether an cancelled invoice has been created for the"
             "Cancellation Policy.")
    digital_sign = fields.Binary(string='Signature', help="Binary field to "
                                                          "store digital "
                                                          "signatures.")
    sign_date = fields.Datetime(
        string='Sign Date',
        help='Date and time of the signature signed.')
    currency_id = fields.Many2one(
        'res.currency', 'Currency',
        default=lambda self: self.env.user.company_id.currency_id.id,
        help="if you select this currency bidding will be on that currency "
             "itself")
    damage_description = fields.Text(string="Damage Description")
    damage_amount = fields.Float(string="Damage Amount",
                                 help="Total Amount for the damages")
    # Responsible
    responsible_id = fields.Many2one(
        'res.users', string='Responsible',
        help='User responsible for managing the rental contract.',
        required=True, tracking=True)

    @api.onchange('pickup_state_id')
    def _onchange_pickup_state(self):
        """
        Automatically updates the 'Pick-Up Country' field based on the selected 'Pick-Up State'.

        When a user selects a state for vehicle pick-up, this method fetches the corresponding
        country from the selected state and sets it in the 'Pick-Up Country' field.
        """
        if self.pickup_state_id:
            self.pickup_country_id = self.pickup_state_id.country_id

    @api.onchange('dropoff_state_id')
    def _onchange_dropoff_state(self):
        """
        Automatically updates the 'Drop-Off Country' field based on the selected 'Drop-Off State'.

        When a user selects a state for vehicle drop-off, this method fetches the corresponding
        country from the selected state and sets it in the 'Drop-Off Country' field.
        """
        if self.dropoff_state_id:
            self.dropoff_country_id = self.dropoff_state_id.country_id

    def _group_expand_states(self, states, domain, order):
        """
        Expands the available group states for selection.
        """
        return ['new', 'in_progress', 'return', 'cancel']

    @api.model
    def create(self, vals_list):
        """
        Override the create method to set a default sequence number if not
        provided.
        """
        if vals_list.get('name', 'New') == 'New':
            vals_list['name'] = self.env['ir.sequence'].next_by_code(
                'vehicle.sequence') or 'New'
        return super().create(vals_list)

    @api.depends('extra_per_hour', 'total_extra_hours', 'extra_per_day',
                 'total_extra_days', 'extra_per_km', 'total_extra_km')
    def _compute_total_extra_charge(self):
        """
        Compute the total extra charge based on the rent type and extra usage
        (hours, days, kilometers).
        """
        for record in self:
            if record.rent_type == 'hours':
                record.total_extra_charge = (record.extra_per_hour *
                                             record.total_extra_hours)
            elif record.rent_type == 'days':
                record.total_extra_charge = (record.extra_per_day *
                                             record.total_extra_days)
            elif record.rent_type == 'kilometers':
                record.total_extra_charge = (
                        record.extra_per_km * record.total_extra_km)
            else:
                record.total_extra_charge = 0

    @api.depends(
        'rent_type',
        'rent_per_hour', 'total_hours',
        'rent_per_day', 'total_days',
        'rent_per_km', 'total_km',
        'driver_charge', 'charge_type',
        'driver_required'
    )
    def _compute_total_rental_charge(self):
        """
        Compute the total rental charge based on the rent type and usage
        (hours, days, kilometers). Include driver charge if applicable.
        """
        for record in self:
            if record.rent_type == 'hours':
                record.total_rental_charge = (
                        record.rent_per_hour * record.total_hours)
            elif record.rent_type == 'days':
                record.total_rental_charge = (
                        record.rent_per_day * record.total_days)
            elif record.rent_type == 'kilometers':
                record.total_rental_charge = (
                        record.rent_per_km * record.total_km)
            else:
                record.total_rental_charge = 0
            if record.charge_type == 'including' and record.driver_required:
                record.total_rental_charge += record.driver_charge

    def action_create_extra_invoice(self):
        """
        Create an invoice for extra charges incurred during the rental period.
        """
        product_id = self.env.ref(
            'advanced_fleet_rental.product_product_vehicle_extra_rental_charge')
        invoice_vals = {
            'partner_id': self.customer_id.id,
            'move_type': 'out_invoice',
            'vehicle_rental_id': self.id,
            'invoice_date': date.today(),
            'invoice_line_ids': [(0, 0, {
                'product_id': product_id.id,
                'name': product_id.name,
                'quantity': 1,
                'price_unit': self.total_extra_charge,
            })],
        }
        invoice = self.env['account.move'].create(invoice_vals)
        invoice.action_post()

    def action_installment(self):
        """
        Generate the rental payment plan based on the selected payment type.
        """
        self.ensure_one()
        self.rental_payment_plan_ids.unlink()
        if self.rent_type == 'kilometers' and self.total_km == 0:
            raise ValidationError(
                _('If the rent type is "kilometers", the total '
                  'kilometers cannot be 0.'))
        if self.rent_type == 'hours' and self.payment_type != 'full':
            raise ValidationError(
                _('If the rent type is "hours", the payment type must be '
                  '"full".'))
        if self.rent_type == 'kilometers' and self.payment_type != 'full':
            raise ValidationError(
                _('If the rent type is "kilometers", the payment type must be '
                  '"full".'))
        if (self.rent_type == 'days' and self.payment_type == 'weekly'
                and self.total_days < 7):
            raise ValidationError(_(
                'The total days are less than a week. '
                'Please select a valid payment type.'))
        if (self.rent_type == 'days' and self.payment_type == 'monthly'
                and self.total_days < 30):
            raise ValidationError(_(
                'The total days are less than a month. '
                'Please select a valid payment type.'))
        pick_up = self.pickup_date
        drop_date = self.dropoff_date
        total_amount = self.total_rental_charge

        if self.payment_type == 'full':
            self.env['rental.payment.plan'].create({
                'contract_id': self.id,
                'invoice_item_id': self.invoice_item_id.id,
                'payment_date': pick_up,
                'payment_amount': total_amount,
                'payment_state': 'not_paid',
            })
            return

        # Calculate interval and number of installments based on rent_type
        if self.rent_type == 'hours':
            amount_per_unit = self.rent_per_hour
            base_interval = relativedelta(hours=1)
        elif self.rent_type == 'days':
            amount_per_unit = self.rent_per_day
            base_interval = relativedelta(days=1)

        if self.payment_type == 'daily':
            payment_interval = relativedelta(days=1)
            current_date = pick_up
        elif self.payment_type == 'weekly':
            payment_interval = relativedelta(weeks=1)
            current_date = pick_up
        elif self.payment_type == 'monthly':
            payment_interval = relativedelta(months=1)
            current_date = pick_up + payment_interval
        else:
            payment_interval = base_interval
        while current_date < drop_date:
            next_date = min(current_date + payment_interval, drop_date)

            # Calculate units in this payment period
            if self.rent_type == 'hours':
                units_in_period = (
                                          next_date - current_date).total_seconds() / 3600
            elif self.rent_type == 'days':
                units_in_period = (next_date - current_date).days

            installment_amount = units_in_period * amount_per_unit

            if installment_amount > 0:
                self.env['rental.payment.plan'].create({
                    'contract_id': self.id,
                    'invoice_item_id': self.invoice_item_id.id,
                    'payment_date': current_date,
                    'payment_amount': installment_amount,
                    'payment_state': 'not_paid',
                })

            current_date = next_date
        # Handle any remaining amount due to rounding
        remaining_amount = total_amount - sum(
            self.rental_payment_plan_ids.mapped('payment_amount'))
        if remaining_amount > 0:
            self.env['rental.payment.plan'].create({
                'contract_id': self.id,
                'invoice_item_id': self.invoice_item_id.id,
                'payment_date': drop_date,
                'payment_amount': remaining_amount,
                'payment_state': 'not_paid',
            })

    @api.depends('pickup_date', 'dropoff_date')
    def _compute_rental_period(self):
        """
        Compute the total rental period in hours and days based on pickup
         and drop-off dates.
        """
        for record in self:
            if record.pickup_date and record.dropoff_date:
                pickup = fields.Datetime.from_string(record.pickup_date)
                dropoff = fields.Datetime.from_string(record.dropoff_date)
                delta = dropoff - pickup

                # Calculate total days
                total_days = delta.days + 1
                record.total_days = total_days

                # Calculate total hours
                total_hours = delta.total_seconds() / 3600
                record.total_hours = total_hours

            else:
                record.total_days = 0
                record.total_hours = 0

    @api.constrains('rent_type', 'pickup_date', 'dropoff_date', 'total_hours',
                    'total_days', )
    def _check_rental_period(self):
        """
        Ensure the drop-off date is not before the pick-up date.
        """
        for record in self:
            if record.pickup_date and record.dropoff_date:
                pickup = fields.Datetime.from_string(record.pickup_date)
                dropoff = fields.Datetime.from_string(record.dropoff_date)
                delta = dropoff - pickup

                if record.rent_type == 'hours':
                    total_hours_computed = delta.total_seconds() / 3600
                    if record.total_hours > total_hours_computed:
                        raise ValidationError(
                            f'The total hours ({record.total_hours})'
                            f' exceed the period between the pickup '
                            f'and dropoff dates.')
                    if record.total_hours == 0:
                        raise ValidationError(
                            f'The total hours cannot be zero.')
                if record.rent_type == 'days':
                    total_days_computed = delta.days + 1
                    if record.total_days > total_days_computed:
                        raise ValidationError(
                            f'The total days ({record.total_days})'
                            f' exceed the period between the pickup '
                            f'and dropoff dates.')
                    if record.total_days == 0:
                        raise ValidationError(
                            f'The total days cannot be zero.')

    def action_account_tab(self):
        """View the Invoices in the Smart Tab."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoices',
            'res_model': 'account.move',
            'target': 'current',
            'domain': [('partner_id', '=', self.customer_id.id),
                       ('vehicle_rental_id', '=', self.id)],
            'view_mode': 'tree,form',
        }

    def _compute_vehicle_to_invoice(self):
        """
        Computes the number of invoices related to the vehicle rental
        contract and updates the 'vehicle_to_invoice_count' field for each record.
        """
        for record in self:
            record.vehicle_to_invoice_count = self.env[
                'account.move'].search_count([
                ('vehicle_rental_id', '=', record.id)
            ])

    def action_extra_invoice_charge(self):
        """
        Creates an invoice for extra services added to the vehicle
        rental contract. If there are no extra services, raises a
        ValidationError.
        """
        if self.extra_service_ids:
            invoice_line_vals = [
                {
                    'product_id': line.product_id.id,
                    'name': line.description or line.product_id.name,
                    'quantity': line.quantity,
                    'price_unit': line.amount,
                }
                for line in self.extra_service_ids
            ]
            invoice_vals = {
                'move_type': 'out_invoice',
                'partner_id': self.customer_id.id,
                'invoice_line_ids': [(0, 0, line) for line in
                                     invoice_line_vals],
                'vehicle_rental_id': self.id,
            }
            invoice = self.env['account.move'].create(invoice_vals)
            invoice.action_post()
            self.is_extra_invoice_created = True
        else:
            raise ValidationError(
                _('Add Extra Services Products.'))

    def action_damage_invoice(self):
        """
        This method opens a new window to link invoices and remove invoices
        for the current sale order.
        """
        return {
            "type": "ir.actions.act_window",
            "name": "Damage Invoices",
            "view_mode": "form",
            "res_model": "damage.invoice",
            "target": "new",
            "context": {
                "default_contract_id": self.id,
            },
        }

    def action_cancel(self):
        """
        Cancels the rental contract by setting its state to 'cancel'.
        """
        self.write({'state': 'cancel'})

    def action_cancel_charges(self):
        """
        Creates an invoice for the cancellation charges based on the contract's
        cancellation policy. The invoice is created using a predefined product
        for cancellation charges. If the cancellation policy is not set,
        it raises a ValidationError.
        """
        if self.cancellation_policy_id:
            product_id = self.env.ref(
                'advanced_fleet_rental.product_product_vehicle_cancel_charge')
            invoice_vals = {
                'partner_id': self.customer_id.id,
                'move_type': 'out_invoice',
                'vehicle_rental_id': self.id,
                'invoice_date': date.today(),
                'invoice_line_ids': [(0, 0, {
                    'product_id': product_id.id,
                    'name': self.cancellation_terms,
                    'quantity': 1,
                    'price_unit': self.cancellation_charge,
                })],
            }
            invoice = self.env['account.move'].create(invoice_vals)
            self.is_cancelled_invoiced = True
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'view_mode': 'form',
                'res_id': invoice.id,
                'target': 'current',
            }
        else:
            raise ValidationError(
                _("No cancellation policy set on the contract."))
