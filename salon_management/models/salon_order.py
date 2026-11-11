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
from datetime import date, timedelta
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from .salon_stage import STAGE_CODES


class SalonOrder(models.Model):
    """Model to create salon orders"""
    _name = 'salon.order'
    _description = 'Salon Order'

    name = fields.Char(string='Salon', required=True, copy=False, readonly=True,
                       default='Draft Salon Order', help="Name of salon order")
    start_time = fields.Datetime(
        default=fields.Datetime.now, required=True,
        help="Start time of the order")
    end_time = fields.Datetime(
        compute='_compute_end_time', store=True, readonly=False,
        help="End time of the order")
    date = fields.Datetime(required=True,
                           default=fields.Datetime.now, help="Registering date")
    color = fields.Integer(default=6,
                           help="Color for the order")
    partner_id = fields.Many2one(
        'res.partner', string="Customer", required=False,
        help="If the customer is a regular customer, then you can add the"
             " customer in your database")
    customer_name = fields.Char(string="Name", required=True,
                                help="Name of salon customer")
    currency_id = fields.Many2one(
        'res.currency', required=True,
        default=lambda self: self.env.company.currency_id.id,
        help="Currency used in the order")
    chair_id = fields.Many2one('salon.chair',
                               required=True, help="Chair for the current "
                                                   "order")
    price_subtotal = fields.Monetary(string='Total', readonly=True, store=True,
                                     compute='_compute_price_subtotal',
                                     help="Total price of order")
    time_taken_total = fields.Float(string='Total time', store=True,
                                    compute='_compute_price_subtotal',
                                    help='Total time taken')
    note = fields.Text(string='Terms and conditions',
                       help="Note for current order")
    order_line_ids = fields.One2many(comodel_name='salon.order.line',
                                     inverse_name='salon_order_id',
                                     string="Order Lines", copy=True,
                                     help='Salon order line for add '
                                          'list of services', required=True)
    stage_id = fields.Many2one(comodel_name='salon.stage', string="State",
                               group_expand='_read_group_stage_ids',
                               default=lambda self: self.env['salon.stage']._get_stage_id('draft'),
                               copy=False, help="state for the salon order(user"
                                                " can add dynamic state from"
                                                " the kanban view)")
    inv_stage_identifier = fields.Boolean(string="Stage Identifier",
                                          help="Field to detect stage")
    stage_code = fields.Selection(
        selection=[(code, code.capitalize()) for code in STAGE_CODES],
        compute='_compute_stage_code',
        help="Technical code of the stage, used by the views")
    validation_controller = fields.Boolean(
        default=False,
        help="Set once the order has been validated")
    booking_identifier = fields.Boolean(help="Field to identify booking")
    user_id = fields.Many2one('res.users', string="Chair User")
    salon_order_created_user = fields.Integer(default=lambda self: self.env.uid,
                                              help="The user whom the salon"
                                                   " order created.")
    count = fields.Integer(string='Invoices', compute='_compute_count',
                           help="Number of invoices of the order")

    def _get_cancelled_stage_id(self):
        """Return the id of the 'Cancelled' stage, if it exists.

        The cancelled stage is looked up dynamically (instead of hardcoding
        an id) so the check keeps working even if stage data hasn't been
        loaded (e.g. when demo data is not installed) or stages are
        reordered.
        """
        return self.env['salon.stage']._get_stage_id('cancelled')

    def _get_conflicting_orders(self):
        """Search for other salon orders using the same chair whose time
        window overlaps with this order's time window.

        Two periods [start_a, end_a] and [start_b, end_b] overlap when
        start_a < end_b and start_b < end_a. Orders with the exact same
        start time are also treated as conflicting, even when the
        duration is zero (e.g. no service lines added yet), since a chair
        physically cannot serve two customers starting at the same moment.
        Cancelled orders are ignored since they no longer occupy the chair.
        """
        self.ensure_one()
        if not self.chair_id or not self.start_time:
            return self.env['salon.order']
        end_time = self.end_time or self.start_time
        domain = [
            ('chair_id', '=', self.chair_id.id),
            ('id', '!=', self.id),
        ]
        cancelled_stage_id = self._get_cancelled_stage_id()
        if cancelled_stage_id:
            domain.append(('stage_id', '!=', cancelled_stage_id))
        domain += [
            '|',
            '&', ('start_time', '<', end_time), ('end_time', '>', self.start_time),
            ('start_time', '=', self.start_time),
        ]
        return self.env['salon.order'].search(domain)

    @api.constrains('chair_id', 'start_time', 'end_time', 'stage_id')
    def _check_chair_double_booking(self):
        """Prevent a chair from being assigned to more than one salon
        order for the same/overlapping time period."""
        cancelled_stage_id = self._get_cancelled_stage_id()
        for order in self:
            if cancelled_stage_id and order.stage_id.id == cancelled_stage_id:
                continue
            conflicts = order._get_conflicting_orders()
            if conflicts:
                conflict = conflicts[0]
                raise ValidationError(self.env._(
                    "Chair '%(chair)s' is already booked on order '%(order)s' "
                    "from %(start)s to %(end)s. A chair cannot have more than "
                    "one salon order for the same period of time.",
                    chair=order.chair_id.name,
                    order=conflict.name,
                    start=conflict.start_time,
                    end=conflict.end_time,
                ))

    @api.depends('order_line_ids.price_subtotal', 'order_line_ids.time_taken')
    def _compute_price_subtotal(self):
        """Compute the subtotal price and the total time of order lines."""
        for order in self:
            order.price_subtotal = sum(
                order.order_line_ids.mapped('price_subtotal'))
            order.time_taken_total = sum(
                order.order_line_ids.mapped('time_taken'))

    @api.depends('start_time', 'time_taken_total')
    def _compute_end_time(self):
        """Derive the end time from the start time and the total time."""
        for order in self:
            order.end_time = (
                order.start_time + timedelta(hours=order.time_taken_total)
                if order.start_time else False)

    @api.depends('stage_id')
    def _compute_stage_code(self):
        """Map the stage to its technical code (based on the XML ids)."""
        stage_ids = {
            self.env['salon.stage']._get_stage_id(code): code
            for code in STAGE_CODES}
        for order in self:
            order.stage_code = stage_ids.get(order.stage_id.id, False)

    def _compute_count(self):
        """Compute invoice count of salon orders"""
        data = self.env['account.move']._read_group(
            [('invoice_origin', 'in', self.mapped('name'))],
            ['invoice_origin'], ['__count'])
        counts = dict(data)
        for order in self:
            order.count = counts.get(order.name, 0)

    def action_view_invoice_salon(self):
        """Function to open invoice for the salon order"""
        self.ensure_one()
        return {'name': self.env._('Invoices'),
                'domain': [('invoice_origin', '=', self.name)],
                'res_model': 'account.move',
                'view_id': False,
                'view_mode': 'list,form',
                'type': 'ir.actions.act_window'}

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        """Return the stages to stage_ids"""
        stage_model = self.env['salon.stage']
        return stage_model.browse(stage_model._search([], order='sequence'))

    def _handle_stage_change(self, target):
        """Validate (and trigger the side effects of) moving this order to
        the ``target`` stage id. Used by drag and drop in the kanban view."""
        self.ensure_one()
        get_stage = self.env['salon.stage']._get_stage_id
        stage_invoiced = get_stage('invoiced')
        stage_closed = get_stage('closed')
        stage_cancelled = get_stage('cancelled')
        stage_draft = get_stage('draft')
        stage_open = get_stage('open')
        current = self.stage_id.id
        if current == stage_invoiced:
            if target != stage_closed:
                raise ValidationError(self.env._("You can't perform that move!"))
            self.chair_id.total_time_taken_chair -= self.time_taken_total
        if current == stage_closed:
            raise ValidationError(
                self.env._("You can't move a salon order from Closed stage!"))
        if current == stage_cancelled:
            raise ValidationError(
                self.env._("You can't move a salon order from Cancel stage!"))
        if current == stage_draft:
            if target not in [stage_open, stage_cancelled]:
                raise ValidationError(self.env._("You can't perform that move!"))
        if current == stage_open:
            if target == stage_cancelled:
                self.chair_id.total_time_taken_chair -= self.time_taken_total
            elif target in [stage_draft, stage_closed]:
                raise ValidationError(self.env._("You can't perform that move!"))
            elif target == stage_invoiced and not self.inv_stage_identifier:
                self.action_create_invoice()
        if self.name == "Draft Salon Order" and target == stage_open:
            self.action_validate()
            self.action_confirm()

    def write(self, values):
        """ Manage drag and drop in salon order kanban view """
        if 'stage_id' in values:
            for order in self:
                order._handle_stage_change(values['stage_id'])
        result = super().write(values)
        if 'stage_id' in values:
            self.update_number_of_orders()
        return result

    def action_confirm(self):
        """Confirm function of salon order"""
        sequence_code = 'salon.order.sequence'
        for order in self:
            order_date = str(order.date)[:10]
            order.name = self.env['ir.sequence'].with_context(
                ir_sequence_date=order_date).next_by_code(sequence_code)
            if order.partner_id:
                order.partner_id.partner_salon = True
            order.stage_id = self.env['salon.stage']._get_stage_id('open')
            order.chair_id.total_time_taken_chair += order.time_taken_total
            order.user_id = order.chair_id.user_id
        self.update_number_of_orders()

    def action_validate(self):
        """ Validate function of salon order"""
        self.validation_controller = True
        self.update_number_of_orders()

    def action_close(self):
        """Close function for salon order"""
        self.stage_id = self.env['salon.stage']._get_stage_id('closed')
        self.update_number_of_orders()

    def action_cancel(self):
        """Function to cancel the salon order"""
        self.stage_id = self.env['salon.stage']._get_stage_id('cancelled')
        self.update_number_of_orders()

    def action_update_total(self):
        """Update total amount in salon order"""
        for order in self:
            amount_untaxed = 0.0
            for line in order.order_line_ids:
                amount_untaxed += line.price_subtotal
            order.price_subtotal = amount_untaxed

    @api.onchange('chair_id')
    def _onchange_chair_id(self):
        """Onchange function of chair_id field"""
        if 'active_id' in self.env.context.keys():
            self.chair_id = self.env.context['active_id']

    def action_create_invoice(self):
        """Function to create invoice"""
        if self.partner_id:
            supplier = self.partner_id
        else:
            # Fall back to the default salon customer (created in data files).
            supplier = self.env.ref(
                'salon_management.res_partner_01', raise_if_not_found=False)
            if not supplier:
                raise UserError(
                    self.env._("No customer selected and the default salon "
                               "customer was not found. Please set a customer "
                               "on the order or restore the default customer."))
        # Use the Salon Service product created by data files.
        product_tmpl = self.env.ref(
            'salon_management.salon_service_product_01',
            raise_if_not_found=False)
        product_id = product_tmpl.product_variant_id if product_tmpl else False
        if not product_id:
            raise UserError(
                self.env._("The 'Salon Service' product was not found. Please "
                           "make sure the master data has been loaded."))
        lines = []
        for records in self.order_line_ids:
            if product_id.property_account_income_id.id:
                income_account = product_id.property_account_income_id.id
            elif product_id.categ_id.property_account_income_categ_id.id:
                income_account = (
                    product_id.categ_id.property_account_income_categ_id.id)
            else:
                raise UserError(
                    self.env._(
                        "Please define an income account for the product "
                        "'%(name)s' (id: %(id)d).",
                        name=product_id.name, id=product_id.id))
            lines.append((0, 0, {
                'name': records.service_id.name,
                'account_id': income_account,
                'price_unit': records.price,
                'quantity': 1,
                'product_id': product_id.id,
            }))
        stage_invoiced = self.env['salon.stage']._get_stage_id('invoiced')
        stage_closed = self.env['salon.stage']._get_stage_id('closed')
        invoice = self.env['account.move'].sudo().create({
            'move_type': 'out_invoice',
            'partner_id': supplier.id,
            'invoice_user_id': self.env.user.id,
            'invoice_origin': self.name,
            'invoice_line_ids': lines,
        })
        result = {
            'name': self.env.ref('account.action_move_out_invoice_type',
                                 raise_if_not_found=False).name,
            'type': 'ir.actions.act_window',
            'views': [[False, 'form']],
            'target': 'current',
            'res_id': invoice.id,
            'res_model': 'account.move',
        }
        self.inv_stage_identifier = True
        self.stage_id = stage_invoiced
        invoiced_stages = [s for s in [stage_invoiced, stage_closed] if s]
        invoiced_records = self.env['salon.order'].search(
            [('stage_id', 'in', invoiced_stages),
             ('chair_id', '=', self.chair_id.id)])
        total = 0
        for rows in invoiced_records:
            invoiced_date = str(rows.date)[:10]
            if invoiced_date == str(date.today()):
                total += rows.price_subtotal
        self.chair_id.collection_today = total
        self.update_number_of_orders()
        return result

    @api.ondelete(at_uninstall=False)
    def _unlink_except_invoiced_or_closed(self):
        """Invoiced or closed salon orders cannot be deleted."""
        stage_invoiced = self.env['salon.stage']._get_stage_id('invoiced')
        stage_closed = self.env['salon.stage']._get_stage_id('closed')
        locked_stages = [s for s in [stage_invoiced, stage_closed] if s]
        for order in self:
            if order.stage_id.id in locked_stages:
                raise UserError(
                    self.env._("You can't delete an invoiced salon order!"))

    def update_number_of_orders(self):
        """ Function to update the number of active orders for the chair."""
        get_stage = self.env['salon.stage']._get_stage_id
        active_stages = [s for s in [get_stage('open'), get_stage('invoiced')]
                         if s]
        for chair in self.chair_id:
            chair.number_of_orders = self.env['salon.order'].search_count(
                [('chair_id', '=', chair.id),
                 ('stage_id', 'in', active_stages)])
