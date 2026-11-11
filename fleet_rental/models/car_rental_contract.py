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
from datetime import date, datetime, timedelta

from markupsafe import Markup, escape

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class CarRentalContract(models.Model):
    _name = 'car.rental.contract'
    _inherit = 'mail.thread'
    _description = 'Fleet Rental Management'

    def _get_fleet_service_product(self):
        """Retrieve configured fleet service product or fallback to default ref."""
        product_id = self.env['ir.config_parameter'].sudo().get_int('fleet_rental.fleet_service_product_id', default=0)
        if product_id:
            product_tmpl = self.env['product.template'].browse(product_id).exists()
            if product_tmpl:
                return product_tmpl
        return self.env.ref('fleet_rental.fleet_service_product', raise_if_not_found=False)

    def _default_journal_type(self):
        return self.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', self.env.company.id),
        ], limit=1)

    def _default_account_type(self):
        product = self._get_fleet_service_product()
        if product and product.property_account_income_id:
            return product.property_account_income_id
        if product and product.categ_id.property_account_income_categ_id:
            return product.categ_id.property_account_income_categ_id
        return self.env['account.account'].search([
            ('account_type', '=', 'income'),
            ('company_ids', 'in', [self.env.company.id]),
        ], limit=1) or self.env['account.account'].search([
            ('account_type', '=', 'income'),
        ], limit=1)

    image = fields.Binary(related='vehicle_id.image_128',
                          string="Image of Vehicle", help="Vehicle Image")
    reserved_fleet_id = fields.Many2one(comodel_name='rental.fleet.reserved', copy=False,
                                        help="Reserved Fleet for this Contact")
    name = fields.Char(default="Draft Contract",
                       readonly=True, copy=False, help="Name of the contract")
    customer_id = fields.Many2one(comodel_name='res.partner',
                                  required=True,
                                  help="Customer")
    vehicle_id = fields.Many2one(comodel_name='fleet.vehicle',
                                 required=True,
                                 help="Vehicle")
    car_brand = fields.Many2one(comodel_name='fleet.vehicle.model.brand',
                                string="Fleet Brand", related='vehicle_id.model_id.brand_id',
                                store=True, readonly=True, help="Manufacture of the fleet")
    car_color = fields.Char(string="Fleet Color", size=50, related='vehicle_id.color', store=True,
                            copy=False, readonly=True, help="Fleet color")
    cost = fields.Float(string="Rent Cost", help="This field determines the cost of rent", required=True)
    rent_start_date = fields.Date(required=True, default=fields.Date.context_today,
                                  help="Start date of contract", tracking=True)
    start_time = fields.Char(string="Start By", help="Enter the contract starting hour", tracking=True)
    end_time = fields.Char(string="End By", help="Enter the contract Ending hour", tracking=True)
    rent_by_hour = fields.Boolean(help="Enable to start contract on hour basis")
    rent_end_date = fields.Date(required=True, help="End date of contract", tracking=True)
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'), ('reserved', 'Reserved'), ('running', 'Running'),
            ('cancel', 'Cancel'), ('checking', 'Checking'), ('invoice', 'Invoice'), ('done', 'Done'),
        ],
        default="draft", copy=False, tracking=True, help="Contract status")
    notes = fields.Text(string="Details & Notes", help="Additional notes about the contract")
    cost_generated = fields.Float(string='Recurring Cost',
                                  help="Costs paid at regular intervals, depending on the cost frequency")
    cost_frequency = fields.Selection(
        selection=[
            ('no', 'No'), ('daily', 'Daily'), ('weekly', 'Weekly'),
            ('monthly', 'Monthly'), ('yearly', 'Yearly'),
        ],
        string="Recurring Cost Frequency",
        help='Frequency of the recurring cost', required=True)
    journal_type = fields.Many2one(
        comodel_name='account.journal', string='Journal', help="Journal type to record.",
        default=lambda self: self._default_journal_type())
    account_type = fields.Many2one(
        comodel_name='account.account', string='Account', help="Account type to record",
        default=lambda self: self._default_account_type())
    recurring_line = fields.One2many(comodel_name='fleet.rental.line', inverse_name='rental_number',
                                     readonly=True, help="Recurring Invoices", copy=False)
    first_payment = fields.Float(tracking=True, required=True,
                                 help="Transaction/Office/Contract charge amount, must paid by customer side "
                                      "other than recurrent payments")
    first_payment_inv = fields.Many2one(comodel_name='account.move', copy=False, help="First invoice for the contract")
    first_invoice_created = fields.Boolean(copy=False, help="Show first invoice")
    attachment_ids = fields.Many2many(
        comodel_name='ir.attachment',
        relation='car_rent_checklist_ir_attachments_rel',
        column1='rental_id',
        column2='attachment_id',
        string="Attachments",
        help="Images of the vehicle before contract/any attachments",
    )
    checklist_line = fields.One2many(
        comodel_name='car.rental.checklist',
        inverse_name='checklist_number',
        string="Checklist",
        help="Facilities/Accessories, That should verify when closing the contract.",
    )
    total = fields.Float(
        string="Total (Accessories/Tools)",
        compute='_compute_totals',
        store=True,
        readonly=True,
        copy=False,
        help="Total amount of the contract.",
    )
    tools_missing_cost = fields.Float(
        string="Missing Cost",
        compute='_compute_totals',
        store=True,
        readonly=True,
        copy=False,
        help='This is the total amount of missing tools/accessories',
    )
    damage_cost = fields.Float(
        string="Damage Cost / Balance Amount",
        help="damage cost",
        copy=False,
    )
    damage_cost_sub = fields.Float(
        string="Subtotal Damage Cost",
        compute='_compute_totals',
        store=True,
        readonly=True,
        copy=False,
        help="Damage sub cost",
    )
    total_cost = fields.Float(
        string="Total",
        compute='_compute_totals',
        store=True,
        readonly=True,
        copy=False,
        help="Total cost of the contract.",
    )
    invoice_count = fields.Integer(
        compute='_compute_invoice_count',
        string='# Invoice',
        copy=False,
        help="Invoice count created",
    )
    sales_person = fields.Many2one(
        comodel_name='res.users',
        default=lambda self: self.env.uid,
        tracking=True,
        help="Sales person for the contract",
    )
    read_only = fields.Boolean(help="To make field read only")
    company_id = fields.Many2one(comodel_name='res.company',
                                 default=lambda self: self.env.company, help="Company this record owns")

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._update_vehicle_state()
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'state' in vals or 'vehicle_id' in vals:
            self._update_vehicle_state()
        return res

    def unlink(self):
        """Clean up reservations and restore vehicle availability when contracts are deleted."""
        vehicles = self.mapped('vehicle_id')
        reservations = self.mapped('reserved_fleet_id')
        if reservations:
            reservations.unlink()
        res = super().unlink()
        active_state = self.env.ref('fleet_rental.vehicle_state_active', raise_if_not_found=False)
        for vehicle in vehicles:
            other_contracts = self.search([
                ('vehicle_id', '=', vehicle.id),
                ('state', 'in', ('reserved', 'running')),
            ])
            if not other_contracts:
                vals = {'rental_check_availability': True}
                if active_state:
                    vals['state_id'] = active_state.id
                vehicle.write(vals)
        return res

    def _update_vehicle_state(self):
        """
            Handle state transitions and update the 'state_id' of the
            associated vehicle based on the value of the 'state' field.
        """
        rent_state = self.env.ref('fleet_rental.vehicle_state_rent', raise_if_not_found=False)
        active_state = self.env.ref('fleet_rental.vehicle_state_active', raise_if_not_found=False)
        for record in self:
            if record.state == "running" and rent_state:
                record.vehicle_id.write({'state_id': rent_state.id})
            elif record.state == "cancel" and active_state:
                record.vehicle_id.write({'state_id': active_state.id})
            elif record.state == "invoice":
                record.rent_end_date = fields.Date.today()
                if active_state:
                    record.vehicle_id.write({'state_id': active_state.id})
            elif record.state == "done" and active_state:
                record.vehicle_id.write({'state_id': active_state.id})

    @api.depends('checklist_line.price', 'checklist_line.checklist_active', 'damage_cost')
    def _compute_totals(self):
        for record in self:
            total = sum(line.price for line in record.checklist_line)
            tools_missing_cost = sum(line.price for line in record.checklist_line if not line.checklist_active)
            record.total = total
            record.tools_missing_cost = tools_missing_cost
            record.damage_cost_sub = record.damage_cost or 0.0
            record.total_cost = tools_missing_cost + (record.damage_cost or 0.0)

    def action_run(self):
        """ Set the state of the object to 'running'. """
        self.state = 'running'

    @api.constrains('rent_start_date', 'rent_end_date')
    def validate_dates(self):
        """
            Check the validity of the 'rent_start_date' and 'rent_end_date'
            fields.
            Raise a ValidationError if 'rent_end_date' is earlier than
            'rent_start_date'.
        """
        for record in self:
            if record.rent_start_date and record.rent_end_date and record.rent_end_date < record.rent_start_date:
                raise ValidationError(self.env._("Please select a valid end date."))

    def set_to_done(self):
        """
            Set the state of the object to 'done' based on certain conditions related to invoices.
            Raise a UserError if certain invoices are pending or if damage/missing tool costs exist.
        """
        invoice_ids = self.env['account.move'].search(
            [('fleet_rent_id', '=', self.id)])
        if any(each.payment_state not in ('paid', 'in_payment') for each in
               invoice_ids):
            raise UserError(self.env._("Some Invoices are pending"))
        if self.state == 'checking' and self.total_cost != 0:
            raise UserError(self.env._(
                "Please verify the checklist to create invoice for damages/missing tools first."))
        if self.reserved_fleet_id:
            self.reserved_fleet_id.unlink()
        self.vehicle_id.rental_check_availability = True
        self.state = 'done'

    def _compute_invoice_count(self):
        """
            Calculate the count of invoices related to the current object.
            Update the 'invoice_count' field accordingly.
        """
        for each in self:
            each.invoice_count = self.env['account.move'].search_count(
                [('fleet_rent_id', '=', each.id)])

    def fleet_scheduler1(self, rent_date):
        """
            Perform actions related to fleet scheduling, including creating
            invoices, managing recurring data, and sending email notifications.
        """
        inv_obj = self.env['account.move']
        recurring_obj = self.env['fleet.rental.line']
        supplier = self.customer_id
        product_tmpl = self._get_fleet_service_product() or self.env.ref('fleet_rental.fleet_service_product')
        product_id = product_tmpl.product_variant_id or product_tmpl.product_variant_ids[:1]
        if product_id.property_account_income_id:
            income_account = product_id.property_account_income_id
        elif product_id.categ_id.property_account_income_categ_id:
            income_account = product_id.categ_id.property_account_income_categ_id
        elif self.account_type:
            income_account = self.account_type
        else:
            raise UserError(
                self.env._('Please define income account for this product: "%(product_name)s" (id:%(product_id)d).',
                           product_name=product_id.name,
                           product_id=product_id.id))
        inv_data = {
            'ref': supplier.name,
            'partner_id': supplier.id,
            'journal_id': self.journal_type.id,
            'invoice_origin': self.name,
            'fleet_rent_id': self.id,
            'invoice_payment_term_id': None,
            'invoice_date_due': self.rent_end_date,
            'move_type': 'out_invoice',
            'invoice_line_ids': [(0, 0, {
                'account_id': income_account.id,
                'price_unit': self.cost_generated,
                'quantity': 1,
                'product_id': product_id.id,
            })],
        }
        inv_id = inv_obj.create(inv_data)

        recurring_data = {
            'name': self.vehicle_id.name,
            'date_today': rent_date,
            'account_info': income_account.name,
            'rental_number': self.id,
            'recurring_amount': self.cost_generated,
            'invoice_number': inv_id.id,
            'invoice_ref': inv_id.id,
        }

        recurring_obj.create(recurring_data)
        mail_content = Markup(self.env._(
            '<h3>Reminder Recurrent Payment!</h3><br/>Hi %(customer)s, <br/> This is to remind you that the '
            'recurrent payment for the rental contract has to be done. '
            'Please make the payment at the earliest.<br/><br/>'
            'Please find the details below:<br/><br/>'
            '<table><tr><td>Contract Ref</td><td>%(contract_ref)s</td></tr>'
            '<tr><td>Amount</td><td>%(amount)s</td></tr>'
            '<tr><td>Due Date</td><td>%(due_date)s</td></tr>'
            '<tr><td>Responsible Person</td><td>%(user_name)s, %(user_phone)s</td></tr></table>',
        )) % {
            'customer': escape(self.customer_id.name or ''),
            'contract_ref': escape(self.name or ''),
            'amount': inv_id.amount_total,
            'due_date': inv_id.invoice_date_due,
            'user_name': escape(inv_id.user_id.name or ''),
            'user_phone': escape(inv_id.user_id.phone or ''),
        }
        main_content = {
            'subject': "Reminder Recurrent Payment!",
            'author_id': self.env.user.partner_id.id,
            'body_html': mail_content,
            'email_to': self.customer_id.email,
        }
        self.env['mail.mail'].create(main_content).send()
        self.message_post(body=mail_content, subject=main_content['subject'])

    @api.model
    def fleet_scheduler(self):
        """
            Perform fleet scheduling operations, including creating invoices,
            managing recurring data, and sending email notifications.
        """
        inv_obj = self.env['account.move']
        recurring_obj = self.env['fleet.rental.line']
        today = date.today()
        for records in self.search([('state', '=', 'running')]):
            start_date = datetime.strptime(str(records.rent_start_date),
                                           '%Y-%m-%d').date()
            end_date = datetime.strptime(str(records.rent_end_date),
                                         '%Y-%m-%d').date()
            if end_date >= date.today():
                temp = 0
                if records.cost_frequency == 'daily':
                    temp = 1
                elif records.cost_frequency == 'weekly':
                    week_days = (date.today() - start_date).days
                    if week_days % 7 == 0 and week_days != 0:
                        temp = 1
                elif records.cost_frequency == 'monthly':
                    if start_date.day == date.today().day and start_date != date.today():
                        temp = 1
                elif records.cost_frequency == 'yearly':
                    if start_date.day == date.today().day and start_date.month == date.today().month and \
                            start_date != date.today():
                        temp = 1
                if temp == 1 and records.cost_frequency != "no" and records.state == "running":
                    supplier = records.customer_id
                    product_tmpl = (
                        self._get_fleet_service_product()
                        or self.env.ref('fleet_rental.fleet_service_product')
                    )
                    product_id = product_tmpl.product_variant_id or product_tmpl.product_variant_ids[:1]
                    if product_id.property_account_income_id:
                        income_account = product_id.property_account_income_id
                    elif product_id.categ_id.property_account_income_categ_id:
                        income_account = product_id.categ_id.property_account_income_categ_id
                    elif records.account_type:
                        income_account = records.account_type
                    else:
                        raise UserError(
                            self.env._(
                                'Please define income account for this product: '
                                '"%(product_name)s" (id:%(product_id)d).',
                                product_name=product_id.name,
                                product_id=product_id.id))
                    inv_data = {
                        'ref': supplier.name,
                        'partner_id': supplier.id,
                        'currency_id': records.account_type.company_currency_id.id,
                        'journal_id': records.journal_type.id,
                        'invoice_origin': records.name,
                        'fleet_rent_id': records.id,
                        'invoice_date': today,
                        'company_id': records.company_id.id,
                        'invoice_payment_term_id': None,
                        'invoice_date_due': records.rent_end_date,
                        'move_type': 'out_invoice',
                        'invoice_line_ids': [(0, 0, {
                            'account_id': income_account.id,
                            'price_unit': records.cost_generated,
                            'quantity': 1,
                            'product_id': product_id.id,
                        })],
                    }
                    inv_id = inv_obj.create(inv_data)
                    recurring_data = {
                        'name': records.vehicle_id.name,
                        'date_today': today,
                        'account_info': income_account.name,
                        'rental_number': records.id,
                        'recurring_amount': records.cost_generated,
                        'invoice_number': inv_id.id,
                        'invoice_ref': inv_id.id,
                    }
                    recurring_obj.create(recurring_data)

                    mail_content = Markup(self.env._(
                        '<h3>Reminder Recurrent Payment!</h3><br/>Hi %(customer)s, <br/> '
                        'This is to remind you that the '
                        'recurrent payment for the rental contract has to be done. '
                        'Please make the payment at the earliest.<br/><br/>'
                        'Please find the details below:<br/><br/>'
                        '<table><tr><td>Contract Ref</td><td>%(contract_ref)s</td></tr>'
                        '<tr><td>Amount</td><td>%(amount)s</td></tr>'
                        '<tr><td>Due Date</td><td>%(due_date)s</td></tr>'
                        '<tr><td>Responsible Person</td><td>%(user_name)s, %(user_phone)s</td></tr></table>',
                    )) % {
                        'customer': escape(records.customer_id.name or ''),
                        'contract_ref': escape(records.name or ''),
                        'amount': inv_id.amount_total,
                        'due_date': inv_id.invoice_date_due,
                        'user_name': escape(inv_id.user_id.name or ''),
                        'user_phone': escape(inv_id.user_id.phone or ''),
                    }
                    main_content = {
                        'subject': "Reminder Recurrent Payment!",
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': records.customer_id.email,
                    }
                    self.env['mail.mail'].create(main_content).send()
                    records.message_post(body=mail_content, subject=main_content['subject'])
            else:
                if records.state == 'running':
                    records.state = "checking"

    def action_verify(self):
        """
            Verifies the damage cost or missing cost
        """
        if self.reserved_fleet_id:
            self.reserved_fleet_id.unlink()
        self.rent_end_date = fields.Date.today()
        self.vehicle_id.rental_check_availability = True
        if self.total_cost != 0:
            self.state = "invoice"
            product_tmpl = self._get_fleet_service_product() or self.env.ref('fleet_rental.fleet_service_product')
            product_id = product_tmpl.product_variant_id or product_tmpl.product_variant_ids[:1]
            if product_id.property_account_income_id:
                income_account = product_id.property_account_income_id
            elif product_id.categ_id.property_account_income_categ_id:
                income_account = product_id.categ_id.property_account_income_categ_id
            elif self.account_type:
                income_account = self.account_type
            else:
                raise UserError(
                    self.env._('Please define income account for this product: "%(product_name)s" (id:%(product_id)d).',
                               product_name=product_id.name,
                               product_id=product_id.id))
            supplier = self.customer_id
            inv_data = {
                'ref': supplier.name,
                'move_type': 'out_invoice',
                'partner_id': supplier.id,
                'currency_id': self.account_type.company_currency_id.id,
                'journal_id': self.journal_type.id,
                'invoice_origin': self.name,
                'fleet_rent_id': self.id,
                'company_id': self.company_id.id,
                'invoice_date_due': self.rent_end_date,
                'invoice_line_ids': [(0, 0, {
                    'name': "Damage/Tools missing cost",
                    'account_id': income_account.id,
                    'price_unit': self.total_cost,
                    'quantity': 1,
                    'product_id': product_id.id,
                })],
            }
            inv_id = self.env['account.move'].create(inv_data)
            return {
                'name': self.env._('Fleet Rental Invoices'),
                'view_mode': 'form',
                'res_model': 'account.move',
                'res_id': inv_id.id,
                'type': 'ir.actions.act_window',
            }
        invoice_ids = self.env['account.move'].search([('fleet_rent_id', '=', self.id)])
        if any(each.payment_state not in ('paid', 'in_payment') for each in invoice_ids):
            self.state = "invoice"
        else:
            self.state = "done"
        return False

    def action_confirm(self):
        """
           Confirm the rental contract, check vehicle availability, update
           state to "reserved," generate a sequence code, and send a
           confirmation email.
        """
        self.vehicle_id.rental_check_availability = False
        check_availability = 0
        for each in self.vehicle_id.rental_reserved_time:
            if each.date_from <= self.rent_start_date <= each.date_to:
                check_availability = 1
            elif self.rent_start_date < each.date_from:
                if each.date_from <= self.rent_end_date <= each.date_to or self.rent_end_date > each.date_to:
                    check_availability = 1
                else:
                    check_availability = 0
            else:
                check_availability = 0
        if check_availability == 0:
            reserved_id = self.vehicle_id.rental_reserved_time.create(
                {'customer_id': self.customer_id.id,
                 'date_from': self.rent_start_date,
                 'date_to': self.rent_end_date,
                 'reserved_obj_id': self.vehicle_id.id,
                 })
            self.write({'reserved_fleet_id': reserved_id.id})
        else:
            raise UserError(
                self.env._('Sorry, this vehicle is already booked by another customer'))
        self.state = "reserved"
        sequence_code = 'car.rental.sequence'
        order_date = self.create_date
        order_date = str(order_date)[0:10]
        self.name = self.env['ir.sequence'] \
            .with_context(ir_sequence_date=order_date).next_by_code(
            sequence_code)
        mail_content = Markup(self.env._(
            '<h3>Order Confirmed!</h3><br/>Hi %(customer)s, <br/> This is to notify that your rental contract has '
            'been confirmed. <br/><br/>'
            'Please find the details below:<br/><br/>'
            '<table><tr><td>Reference Number</td><td>%(contract_ref)s</td></tr>'
            '<tr><td>Time Range</td><td>%(date_from)s to %(date_to)s</td></tr>'
            '<tr><td>Vehicle</td><td>%(vehicle_name)s</td></tr>'
            '<tr><td>Point Of Contact</td><td>%(user_name)s, %(user_phone)s</td></tr></table>',
        )) % {
            'customer': escape(self.customer_id.name or ''),
            'contract_ref': escape(self.name or ''),
            'date_from': escape(str(self.rent_start_date or '')),
            'date_to': escape(str(self.rent_end_date or '')),
            'vehicle_name': escape(self.vehicle_id.name or ''),
            'user_name': escape(self.sales_person.name or ''),
            'user_phone': escape(self.sales_person.phone or ''),
        }
        main_content = {
            'subject': self.env._('Confirmed: %(contract)s - %(vehicle)s',
                                  contract=self.name or '',
                                  vehicle=self.vehicle_id.name or ''),
            'author_id': self.env.user.partner_id.id,
            'body_html': mail_content,
            'email_to': self.customer_id.email,
        }
        self.env['mail.mail'].create(main_content).send()
        self.message_post(body=mail_content, subject=main_content['subject'])

    def action_cancel(self):
        """
           Cancel the rental contract.
           Update the state to "cancel" and delete the associated reserved
           fleet ID if it exists.
       """
        self.state = "cancel"
        self.vehicle_id.rental_check_availability = True
        if self.reserved_fleet_id:
            self.reserved_fleet_id.unlink()

    def force_checking(self):
        """
            Force the checking of payment status for associated invoices.
            If all invoices are marked as paid, update the state to "checking."
            Otherwise, raise a UserError indicating that some invoices are
            pending.
        """
        invoice_ids = self.env['account.move'].search(
            [('fleet_rent_id', '=', self.id)])
        if any(each.payment_state not in ('paid', 'in_payment') for each in invoice_ids):
            raise UserError(self.env._("Some Invoices are pending"))
        self.state = "checking"

    def action_view_invoice(self):
        """
            Display the associated invoices for the current record.
            Construct the appropriate view configurations based on the number
            of invoices found.
        """
        inv_obj = self.env['account.move'].search(
            [('fleet_rent_id', '=', self.id)])
        inv_ids = []
        for each in inv_obj:
            inv_ids.append(each.id)
        view_id = self.env.ref('account.view_move_form').id
        if inv_ids:
            if len(inv_ids) <= 1:
                value = {
                    'view_mode': 'form',
                    'res_model': 'account.move',
                    'view_id': view_id,
                    'type': 'ir.actions.act_window',
                    'name': self.env._('Invoice'),
                    'res_id': inv_ids and inv_ids[0],
                }
            else:
                value = {
                    'domain': [('fleet_rent_id', '=', self.id)],
                    'view_mode': 'list,form',
                    'res_model': 'account.move',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'name': self.env._('Invoice'),
                }
            return value
        return False

    def action_invoice_create(self):
        """
            Create an invoice for the rental contract.
            Calculate the rental duration and iterate over each day to create
            invoices.
            Create the first payment invoice, add relevant invoice line data,
            and send an email notification for the received payment.
        """
        for each in self:
            rent_date = self.rent_start_date
            if each.cost_frequency != 'no' and rent_date < date.today():
                rental_days = (date.today() - rent_date).days
                if each.cost_frequency == 'weekly':
                    rental_days = int(rental_days / 7)
                if each.cost_frequency == 'monthly':
                    rental_days = int(rental_days / 30)
                if each.cost_frequency == 'yearly':
                    rental_days = int(rental_days / 365)
                for each1 in range(0, rental_days + 1):
                    if rent_date > datetime.strptime(str(each.rent_end_date),
                                                     "%Y-%m-%d").date():
                        break
                    each.fleet_scheduler1(rent_date)
                    if each.cost_frequency == 'daily':
                        rent_date = rent_date + timedelta(days=1)
                    if each.cost_frequency == 'weekly':
                        rent_date = rent_date + timedelta(days=7)
                    if each.cost_frequency == 'monthly':
                        rent_date = rent_date + timedelta(days=30)
                    if each.cost_frequency == 'yearly':
                        rent_date = rent_date + timedelta(days=365)
        self.first_invoice_created = True
        inv_obj = self.env['account.move']
        supplier = self.customer_id
        inv_data = {
            'ref': supplier.name,
            'move_type': 'out_invoice',
            'partner_id': supplier.id,
            'currency_id': self.account_type.company_currency_id.id,
            'journal_id': self.journal_type.id,
            'invoice_origin': self.name,
            'fleet_rent_id': self.id,
            'company_id': self.company_id.id,
            'invoice_date_due': self.rent_end_date,
            'is_first_invoice': True,
        }
        inv_id = inv_obj.create(inv_data)
        self.first_payment_inv = inv_id.id
        product_tmpl = self._get_fleet_service_product() or self.env.ref('fleet_rental.fleet_service_product')
        product_id = product_tmpl.product_variant_id or product_tmpl.product_variant_ids[:1]
        if product_id.property_account_income_id:
            income_account = product_id.property_account_income_id.id
        elif product_id.categ_id.property_account_income_categ_id:
            income_account = product_id.categ_id.property_account_income_categ_id.id
        elif self.account_type:
            income_account = self.account_type.id
        else:
            raise UserError(
                self.env._('Please define income account for this product: "%(product_name)s" (id:%(product_id)d).',
                           product_name=product_id.name,
                           product_id=product_id.id))
        if inv_id:
            list_value = [(0, 0, {
                'name': self.vehicle_id.name,
                'price_unit': self.first_payment,
                'quantity': 1.0,
                'account_id': income_account,
                'product_id': product_id.id,
                'move_id': inv_id.id,
            })]
            inv_id.write({'invoice_line_ids': list_value})
        action = self.env.ref('account.action_move_out_invoice_type')
        return {
            'name': action.name,
            'type': 'ir.actions.act_window',
            'views': [[False, 'form']],
            'target': 'current',
            'res_id': inv_id.id,
            'res_model': 'account.move',
        }

    def action_extend_rent(self):
        """
            Set the 'read_only' attribute to True, indicating that the rent
            extension action is being performed and the corresponding fields
            should be made read-only.

            This method is typically used in the context of extending a rental
            agreement.
        """
        self.read_only = True

    def action_confirm_extend_rent(self):
        """
            Confirm the extension of a rental agreement and update the rental
            reserved time for the associated vehicle.

            This method sets the 'date_to' field of the rental reserved time
            for the vehicle to the specified 'rent_end_date', indicating the
            extended rental period. After confirming the extension, the
            'read_only' attribute is set to False to allow further
            modifications.

            This method is typically called when a user confirms the extension
            of a rental.
        """
        self.vehicle_id.rental_reserved_time.write(
            {
                'date_to': self.rent_end_date,
            })
        self.read_only = False

    @api.constrains('start_time', 'end_time', 'rent_start_date',
                    'rent_end_date', 'rent_by_hour')
    def validate_time(self):
        """
            Validate the time constraints for a rental agreement.

            This method is used as a constraint to ensure that the specified
            start and end times are valid, especially when renting by the hour.
            If renting by the hour, it checks whether the end time is greater
            than the start time when the rental start and end
            dates are the same.

            :raises ValidationError: If the time constraints are not met, a
                                    validation error is raised with a relevant
                                     error message.
        """
        for record in self:
            if record.rent_by_hour and record.start_time and record.end_time:
                start_time = datetime.strptime(record.start_time, "%H:%M").time()
                end_time = datetime.strptime(record.end_time, "%H:%M").time()
                if record.rent_end_date == record.rent_start_date and end_time <= start_time:
                    raise ValidationError(self.env._("Please choose a different end time"))

    @api.constrains('rent_end_date')
    def validate_on_read_only(self):
        for record in self:
            if record.read_only and record.reserved_fleet_id:
                old_date = record.reserved_fleet_id.date_to
                if record.rent_end_date <= old_date:
                    raise ValidationError(
                        self.env._("Please choose a date greater than %(old_date)s", old_date=old_date))

    def action_discard_extend(self):
        """
            Validate the 'rent_end_date' when the rental agreement is in
            read-only mode.
            This constraint checks if the rental agreement is marked as
            read-only, indicating that it has been extended or modified. If in
            read-only mode, it compares the 'rent_end_date' with the existing
            'date_to' value in the rental reserved time of the associated
            vehicle. It ensures that the 'rent_end_date' is greater than the
            existing date to maintain consistency.
            :raises ValidationError: If the 'rent_end_date' is not greater than
                                    the existing 'date_to', a validation error
                                    is raised with a relevant error message.
        """
        self.read_only = False
        self.rent_end_date = self.vehicle_id.rental_reserved_time.date_to
