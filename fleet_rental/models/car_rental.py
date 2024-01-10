# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technogies @cybrosys(odoo@cybrosys.com)
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
from datetime import datetime, date, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning, ValidationError


class CarRentalContract(models.Model):
    _name = 'car.rental.contract'
    _description = 'Fleet Rental Management'
    _inherit = 'mail.thread'

    image = fields.Binary(related='vehicle_id.image_128',
                          string="Image of Vehicle")
    reserved_fleet_id = fields.Many2one('rental.fleet.reserved',
                                        invisible=True, copy=False)
    name = fields.Char(string="Name", default="Draft Contract", readonly=True,
                       copy=False)
    customer_id = fields.Many2one('res.partner', required=True,
                                  string='Customer', help="Customer")
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle",
                                 required=True, help="Vehicle",
                                 readonly=True,
                                 states={'draft': [('readonly', False)]}
                                 )
    car_brand = fields.Many2one('fleet.vehicle.model.brand',
                                string="Fleet Brand", size=50,
                                related='vehicle_id.model_id.brand_id',
                                store=True, readonly=True)
    car_color = fields.Char(string="Fleet Color", size=50,
                            related='vehicle_id.color', store=True, copy=False,
                            default='#FFFFFF', readonly=True)
    cost = fields.Float(string="Rent Cost",
                        help="This fields is to determine the cost of rent",
                        required=True)
    rent_start_date = fields.Date(string="Rent Start Date", required=True,
                                  default=str(date.today()),
                                  help="Start date of contract",
                                  track_visibility='onchange')
    start_time = fields.Char(string="Start By",
                             help="Enter the contract starting hour")
    end_time = fields.Char(string="End By",
                           help="Enter the contract Ending hour")
    rent_by_hour = fields.Boolean(string="Rent By Hour",
                                  help="Enable to start contract on "
                                       "hour basis")
    rent_end_date = fields.Date(string="Rent End Date", required=True,
                                help="End date of contract",
                                track_visibility='onchange')
    state = fields.Selection(
        [('draft', 'Draft'), ('reserved', 'Reserved'), ('running', 'Running'),
         ('cancel', 'Cancel'),
         ('checking', 'Checking'), ('invoice', 'Invoice'), ('done', 'Done')],
        string="State",
        default="draft", copy=False, track_visibility='onchange')
    notes = fields.Text(string="Details & Notes")
    cost_generated = fields.Float(string='Recurring Cost',
                                  help="Costs paid at regular intervals, depending on the cost frequency")
    cost_frequency = fields.Selection(
        [('no', 'No'), ('daily', 'Daily'), ('weekly', 'Weekly'),
         ('monthly', 'Monthly'),
         ('yearly', 'Yearly')], string="Recurring Cost Frequency",
        help='Frequency of the recurring cost', required=True)
    journal_type = fields.Many2one('account.journal', 'Journal',
                                   default=lambda self: self.env[
                                       'account.journal'].search(
                                       [('id', '=', 1)]))
    account_type = fields.Many2one('account.account', 'Account',
                                   default=lambda self: self.env[
                                       'account.account'].search(
                                       [('id', '=', 17)]))
    recurring_line = fields.One2many('fleet.rental.line', 'rental_number',
                                     readonly=True, help="Recurring Invoices",
                                     copy=False)
    first_payment = fields.Float(string='First Payment',
                                 help="Transaction/Office/Contract charge "
                                      "amount, must paid by customer side "
                                      "other "
                                      "than recurrent payments",
                                 track_visibility='onchange',
                                 required=True)
    first_payment_inv = fields.Many2one('account.move', copy=False)
    first_invoice_created = fields.Boolean(string="First Invoice Created",
                                           invisible=True, copy=False)
    attachment_ids = fields.Many2many('ir.attachment',
                                      'car_rent_checklist_ir_attachments_rel',
                                      'rental_id', 'attachment_id',
                                      string="Attachments",
                                      help="Images of the vehicle before "
                                           "contract/any attachments")
    checklist_line = fields.One2many('car.rental.checklist',
                                     'checklist_number', string="Checklist",
                                     help="Facilities/Accessories, That should"
                                          " verify when closing the contract.",
                                     states={'invoice': [('readonly', True)],
                                             'done': [('readonly', True)],
                                             'cancel': [('readonly', True)]})
    total = fields.Float(string="Total (Accessories/Tools)", readonly=True,
                         copy=False)
    tools_missing_cost = fields.Float(string="Missing Cost", readonly=True,
                                      copy=False,
                                      help='This is the total amount of '
                                           'missing tools/accessories')
    damage_cost = fields.Float(string="Damage Cost / Balance Amount",
                               copy=False)
    damage_cost_sub = fields.Float(string="Damage Cost / Balance Amount",
                                   readonly=True,
                                   copy=False)
    total_cost = fields.Float(string="Total", readonly=True, copy=False)
    invoice_count = fields.Integer(compute='_invoice_count',
                                   string='# Invoice', copy=False)
    check_verify = fields.Boolean(compute='check_action_verify', copy=False)
    sales_person = fields.Many2one('res.users', string='Sales Person',
                                   default=lambda self: self.env.uid,
                                   track_visibility='always')
    read_only = fields.Boolean(string="Read Only", help="To make field read "
                                                        "only")

    def action_run(self):
        """
            Set the state of the object to 'running'.
        """
        self.state = 'running'

    @api.depends('checklist_line.checklist_active')
    def check_action_verify(self):
        """
            Update the 'check_verify' field based on the value of
            'checklist_active' in 'checklist_line'.
        """
        flag = 0
        for each in self:
            for i in each.checklist_line:
                if i.checklist_active:
                    continue
                else:
                    flag = 1
            if flag == 1:
                each.check_verify = False
            else:
                each.check_verify = True

    @api.constrains('rent_start_date', 'rent_end_date')
    def validate_dates(self):
        """
            Check the validity of the 'rent_start_date' and 'rent_end_date'
            fields.
            Raise a warning if 'rent_end_date' is earlier than
            'rent_start_date'.
        """
        if self.rent_end_date < self.rent_start_date:
            raise UserError("Please select the valid end date.")

    def set_to_done(self):
        """
            Set the state of the object to 'done' based on certain conditions related to invoices.
            Raise a UserError if certain invoices are pending or the total cost is zero.
        """
        invoice_ids = self.env['account.move'].search(
            [('fleet_rent_id', '=', self.id),
             ('amount_untaxed_signed', '=', self.total_cost),
             ('invoice_line_ids.name', '=', 'Damage/Tools missing cost')])
        if any(each.payment_state == 'paid' for each in
               invoice_ids) or self.total_cost == 0:
            self.state = 'done'
        else:
            raise UserError("Some Invoices are pending")

    def _invoice_count(self):
        """
            Calculate the count of invoices related to the current object.
            Update the 'invoice_count' field accordingly.
        """
        self.invoice_count = self.env['account.move'].search_count(
            [('fleet_rent_id', '=', self.id)])

    @api.constrains('state')
    def state_changer(self):
        """
            Handle state transitions and update the 'state_id' of the
            associated vehicle based on the value of the 'state' field.
        """
        if self.state == "running":
            state_id = self.env.ref('fleet_rental.vehicle_state_rent').id
            self.vehicle_id.write({'state_id': state_id})
        elif self.state == "cancel":
            state_id = self.env.ref('fleet_rental.vehicle_state_active').id
            self.vehicle_id.write({'state_id': state_id})
        elif self.state == "invoice":
            self.rent_end_date = fields.Date.today()
            state_id = self.env.ref('fleet_rental.vehicle_state_active').id
            self.vehicle_id.write({'state_id': state_id})

    @api.constrains('checklist_line', 'damage_cost')
    def total_updater(self):
        """
           Update various fields related to totals based on the values in
           'checklist_line', 'damage_cost', and other relevant fields.
       """
        total = 0.0
        tools_missing_cost = 0.0
        for records in self.checklist_line:
            total += records.price
            if not records.checklist_active:
                tools_missing_cost += records.price
        self.total = total
        self.tools_missing_cost = tools_missing_cost
        self.damage_cost_sub = self.damage_cost
        self.total_cost = tools_missing_cost + self.damage_cost

    def fleet_scheduler1(self, rent_date):
        """
            Perform actions related to fleet scheduling, including creating
            invoices, managing recurring data, and sending email notifications.
        """
        inv_obj = self.env['account.move']
        inv_line_obj = self.env['account.move.line']
        recurring_obj = self.env['fleet.rental.line']
        supplier = self.customer_id
        inv_data = {
            'ref': supplier.name,
            'partner_id': supplier.id,
            'invoice_origin': self.name,
            'invoice_date_due': self.rent_end_date,
        }
        inv_id = inv_obj.create(inv_data)
        product_id = self.env['product.product'].search(
            [("name", "=", "Fleet Rental Service")])
        if product_id.property_account_income_id.id:
            income_account = product_id.property_account_income_id
        elif product_id.categ_id.property_account_income_categ_id.id:
            income_account = product_id.categ_id.property_account_income_categ_id
        else:
            raise UserError(
                _('Please define income account for this product: "%s" (id:%d).') % (
                    product_id.name,
                    product_id.id))
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
        inv_line_data = {
            'name': self.vehicle_id.name,
            'account_id': income_account.id,
            'price_unit': self.cost_generated,
            'quantity': 1,
            'product_id': product_id.id,
            'move_id': inv_id.id,
        }
        inv_line_obj.update(inv_line_data)
        mail_content = _(
            '<h3>Reminder Recurrent Payment!</h3><br/>Hi %s, <br/> This is to remind you that the '
            'recurrent payment for the '
            'rental contract has to be done.'
            'Please make the payment at the earliest.'
            '<br/><br/>'
            'Please find the details below:<br/><br/>'
            '<table><tr><td>Contract Ref<td/><td> %s<td/><tr/>'
            '<tr/><tr><td>Amount <td/><td> %s<td/><tr/>'
            '<tr/><tr><td>Due Date <td/><td> %s<td/><tr/>'
            '<tr/><tr><td>Responsible Person <td/><td> %s, %s<td/><tr/><table/>') % \
                       (self.customer_id.name, self.name, inv_id.amount_total,
                        inv_id.invoice_date_due,
                        inv_id.user_id.name,
                        inv_id.user_id.mobile)
        main_content = {
            'subject': "Reminder Recurrent Payment!",
            'author_id': self.env.user.partner_id.id,
            'body_html': mail_content,
            'email_to': self.customer_id.email,
        }
        self.env['mail.mail'].create(main_content).send()

    @api.model
    def fleet_scheduler(self):
        """
            Perform fleet scheduling operations, including creating invoices,
            managing recurring data, and sending email notifications.
        """
        inv_obj = self.env['account.move']
        inv_line_obj = self.env['account.move.line']
        recurring_obj = self.env['fleet.rental.line']
        today = date.today()
        for records in self.search([]):
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
                    inv_data = {
                        'ref': supplier.name,
                        'partner_id': supplier.id,
                        'currency_id': records.account_type.company_id.currency_id.id,
                        'journal_id': records.journal_type.id,
                        'invoice_origin': records.name,
                        'fleet_rent_id': records.id,
                        'company_id': records.account_type.company_id.id,
                        'invoice_date_due': self.rent_end_date,
                    }
                    inv_id = inv_obj.create(inv_data)
                    product_id = self.env['product.product'].search(
                        [("name", "=", "Fleet Rental Service")])
                    if product_id.property_account_income_id.id:
                        income_account = product_id.property_account_income_id
                    elif product_id.categ_id.property_account_income_categ_id.id:
                        income_account = product_id.categ_id.property_account_income_categ_id
                    else:
                        raise UserError(
                            _('Please define income account for this product: "%s" (id:%d).') % (
                                product_id.name,
                                product_id.id))
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
                    inv_line_data = {
                        'name': records.vehicle_id.name,
                        'account_id': income_account.id,
                        'price_unit': records.cost_generated,
                        'quantity': 1,
                        'product_id': product_id.id,
                        'move_id': inv_id.id,

                    }
                    inv_line_obj.update(inv_line_data)
                    mail_content = _(
                        '<h3>Reminder Recurrent Payment!</h3><br/>Hi %s, <br/> This is to remind you that the '
                        'recurrent payment for the '
                        'rental contract has to be done.'
                        'Please make the payment at the earliest.'
                        '<br/><br/>'
                        'Please find the details below:<br/><br/>'
                        '<table><tr><td>Contract Ref<td/><td> %s<td/><tr/>'
                        '<tr/><tr><td>Amount <td/><td> %s<td/><tr/>'
                        '<tr/><tr><td>Due Date <td/><td> %s<td/><tr/>'
                        '<tr/><tr><td>Responsible Person <td/><td> %s, %s<td/><tr/><table/>') % \
                                   (self.customer_id.name, self.name,
                                    inv_id.amount_total,
                                    inv_id.invoice_date_due,
                                    inv_id.user_id.name,
                                    inv_id.user_id.mobile)
                    main_content = {
                        'subject': "Reminder Recurrent Payment!",
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': self.customer_id.email,
                    }
                    self.env['mail.mail'].create(main_content).send()
            else:
                if self.state == 'running':
                    records.state = "checking"

    def action_verify(self):
        self.state = "invoice"
        self.reserved_fleet_id.unlink()
        self.rent_end_date = fields.Date.today()
        self.vehicle_id.rental_check_availability = True
        product_id = self.env['product.product'].search(
            [("name", "=", "Fleet Rental Service")])
        if product_id.property_account_income_id.id:
            income_account = product_id.property_account_income_id
        elif product_id.categ_id.property_account_income_categ_id.id:
            income_account = product_id.categ_id.property_account_income_categ_id
        else:
            raise UserError(
                _('Please define income account for this product: "%s" (id:%d).') % (
                    product_id.name,
                    product_id.id))
        if self.total_cost != 0:
            supplier = self.customer_id
            inv_data = {
                'ref': supplier.name,
                'move_type': 'out_invoice',
                'partner_id': supplier.id,
                'currency_id': self.account_type.company_id.currency_id.id,
                'journal_id': self.journal_type.id,
                'invoice_origin': self.name,
                'fleet_rent_id': self.id,
                'company_id': self.account_type.company_id.id,
                'invoice_date_due': self.rent_end_date,
                'invoice_line_ids': [(0, 0, {
                    'name': "Damage/Tools missing cost",
                    'account_id': income_account.id,
                    'price_unit': self.total_cost,
                    'quantity': 1,
                    'product_id': product_id.id,
                })]
            }
            inv_id = self.env['account.move'].create(inv_data)
            list_view_id = self.env.ref('account.view_move_form', False)
            form_view_id = self.env.ref('account.view_move_tree', False)
            result = {
                'name': 'Fleet Rental Invoices',
                'view_mode': 'form',
                'res_model': 'account.move',
                'type': 'ir.actions.act_window',
                'views': [(list_view_id.id, 'tree'),
                          (form_view_id.id, 'form')],
            }
            if len(inv_id) > 1:
                result['domain'] = "[('id','in',%s)]" % inv_id.ids
            else:
                result = {'type': 'ir.actions.act_window_close'}
            return result

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
                if each.date_from <= self.rent_end_date <= each.date_to:
                    check_availability = 1
                elif self.rent_end_date > each.date_to:
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
                 'reserved_obj': self.vehicle_id.id
                 })
            self.write({'reserved_fleet_id': reserved_id.id})
        else:
            raise UserError(
                'Sorry This vehicle is already booked by another customer')
        self.state = "reserved"
        sequence_code = 'car.rental.sequence'
        order_date = self.create_date
        order_date = str(order_date)[0:10]
        self.name = self.env['ir.sequence'] \
            .with_context(ir_sequence_date=order_date).next_by_code(
            sequence_code)
        mail_content = _(
            '<h3>Order Confirmed!</h3><br/>Hi %s, <br/> This is to notify that your rental contract has '
            'been confirmed. <br/><br/>'
            'Please find the details below:<br/><br/>'
            '<table><tr><td>Reference Number<td/><td> %s<td/><tr/>'
            '<tr><td>Time Range <td/><td> %s to %s <td/><tr/><tr><td>Vehicle <td/><td> %s<td/><tr/>'
            '<tr><td>Point Of Contact<td/><td> %s , %s<td/><tr/><table/>') % \
                       (self.customer_id.name, self.name, self.rent_start_date,
                        self.rent_end_date,
                        self.vehicle_id.name, self.sales_person.name,
                        self.sales_person.mobile)
        main_content = {
            'subject': _('Confirmed: %s - %s') %
                       (self.name, self.vehicle_id.name),
            'author_id': self.env.user.partner_id.id,
            'body_html': mail_content,
            'email_to': self.customer_id.email,
        }
        self.env['mail.mail'].create(main_content).send()

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
            [('fleet_rent_id', '=', self.id),
             ('amount_untaxed_signed', '=', self.first_payment)])
        if any(each.payment_state == 'paid' for each in invoice_ids):
            self.state = "checking"
        else:
            raise UserError("Some Invoices are pending")

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
                    'domain': [('fleet_rent_id', '=', self.id)],
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'account.move',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'name': _('Invoice'),
                }
            return value

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
        self.first_invoice_created = True
        inv_obj = self.env['account.move']
        supplier = self.customer_id
        inv_data = {
            'ref': supplier.name,
            'move_type': 'out_invoice',
            'partner_id': supplier.id,
            'currency_id': self.account_type.company_id.currency_id.id,
            'journal_id': self.journal_type.id,
            'invoice_origin': self.name,
            'fleet_rent_id': self.id,
            'company_id': self.account_type.company_id.id,
            'invoice_date_due': self.rent_end_date,
        }
        inv_id = inv_obj.create(inv_data)
        self.first_payment_inv = inv_id.id
        product_id = self.env['product.product'].search(
            [("name", "=", "Fleet Rental Service")])
        if product_id.property_account_income_id.id:
            income_account = product_id.property_account_income_id.id
        elif product_id.categ_id.property_account_income_categ_id.id:
            income_account = product_id.categ_id.property_account_income_categ_id.id
        else:
            raise UserError(
                _('Please define income account for this product: "%s" (id:%d).') % (
                    product_id.name,
                    product_id.id))

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
        mail_content = _(
            '<h3>First Payment Received!</h3><br/>Hi %s, <br/> This is to notify that your first payment has '
            'been received. <br/><br/>'
            'Please find the details below:<br/><br/>'
            '<table><tr><td>Invoice Number<td/><td> %s<td/><tr/>'
            '<tr><td>Date<td/><td> %s <td/><tr/><tr><td>Amount <td/><td> %s<td/><tr/><table/>') % (
                           self.customer_id.name, inv_id.payment_reference,
                           inv_id.invoice_date, inv_id.amount_total)
        main_content = {
            'subject': _('Payment Received: %s') % inv_id.payment_reference,
            'author_id': self.env.user.partner_id.id,
            'body_html': mail_content,
            'email_to': self.customer_id.email,
        }
        self.env['mail.mail'].create(main_content).send()
        action = self.env.ref('account.action_move_out_invoice_type')
        result = {
            'name': action.name,
            'type': 'ir.actions.act_window',
            'views': [[False, 'form']],
            'target': 'current',
            'res_id': inv_id.id,
            'res_model': 'account.move',
        }
        return result

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
                    'rent_end_date')
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
        if self.rent_by_hour:
            start_time = datetime.strptime(self.start_time, "%H:%M").time()
            end_time = datetime.strptime(self.end_time, "%H:%M").time()
            if (self.rent_end_date == self.rent_start_date and
                    end_time <= start_time):
                raise ValidationError("Please choose a different end time")

    @api.constrains('rent_end_date')
    def validate_on_read_only(self):
        old_date = self.vehicle_id.rental_reserved_time.date_to
        if self.read_only:
            if self.rent_end_date <= old_date:
                raise ValidationError(
                    f"Please choose a date greater that {old_date}")

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
