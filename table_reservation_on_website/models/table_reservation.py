# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from datetime import date, datetime, timedelta
import re
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class TableReservation(models.Model):
    """ Create new model table reservation """
    _name = "table.reservation"
    _description = 'Table Reservation'
    _rec_name = 'sequence'

    sequence = fields.Char(string='Sequence', default=_('New'), readonly=True,
                           copy=False, help="Sequence number for records")
    customer_id = fields.Many2one(comodel_name="res.partner",
                                  string="Customer",
                                  help="Name of the customer")
    floor_id = fields.Many2one(comodel_name='restaurant.floor',
                               string="Floor Plan",
                               help="Booked floor", required=True)
    booked_tables_ids = fields.Many2many(comodel_name='restaurant.table',
                                         string="Tables", required=True,
                                         help="Booked tables")
    date = fields.Date(string="Date", help="Date of reservation",
                       required=True)
    starting_at = fields.Char(string="Starting At",
                              help="starting time of reservation",
                              required=True)
    ending_at = fields.Char(string="Ending At",
                            help="Ending time of reservation",
                            required=True)
    booking_amount = fields.Float(string="Booking Charge",
                                  help="Amount for booking", store=True,
                                  compute="_compute_booking_amount")
    state = fields.Selection([('draft', "Draft"), ('reserved', 'Reserved'),
                              ('done', "Done"), ("cancel", "Cancelled")],
                             default='draft', string="Status",
                             help="State for records")
    type = fields.Selection(string='Order Type',
                            selection=[('website', 'Website'), ('pos', 'POS')],
                            help="The type of Order")
    lead_time = fields.Float(string='Lead time',
                             compute="_compute_lead_time",
                             store=True, readonly=False,
                             help="The order should be reserved hours before"
                                  " the booking start time")
    lead_time_computed = fields.Boolean(string="Lead Time Computed",
                                        default=False)
    order_name = fields.Char(string='Order Name',
                             help='pos order name')

    @api.depends('lead_time_computed')
    def _compute_lead_time(self):
        """ Default lead time for reservations """
        for rec in self:
            if not rec.lead_time_computed:
                is_lead_time = self.env['ir.config_parameter'].sudo().get_param(
                    'table_reservation_on_website.is_lead_time')
                if is_lead_time and rec.lead_time == 0:
                    lead_times = self.env[
                        'ir.config_parameter'].sudo().get_param(
                        'table_reservation_on_website.reservation_lead_time')
                    if lead_times:
                        rec.lead_time = lead_times
                        rec.lead_time_computed = True

    @api.model
    def create(self, vals):
        """ Super create function to add sequence number """
        vals['sequence'] = self.env['ir.sequence'].next_by_code(
            "table.reservation")
        return super(TableReservation, self).create(vals)

    @api.onchange('starting_at', 'ending_at')
    def _onchange_time(self):
        """ Pattern for time """
        for record in self:
            if record.starting_at:
                pattern = r'^([01]\d|2[0-3]):([0-5]\d)$'
                if not re.match(pattern, record.starting_at):
                    raise UserError(_("Invalid time format! [ "
                                      "format HH:MM]"))
            if record.ending_at:
                pattern = r'^([01]\d|2[0-3]):([0-5]\d)$'
                if not re.match(pattern, record.ending_at):
                    raise UserError(_("Invalid time format! [ "
                                      "format HH:MM]"))

    @api.onchange("floor_id")
    def _onchange_floor_id(self):
        """ To show the tables corresponding the floor """
        tables = self.env['restaurant.table'].search([('floor_id', '=',
                                                       self.floor_id.id)])
        table_inbetween = []
        reserved = self.search([('floor_id', '=', self.floor_id.id),
                                ('date', '=', self.date),
                                ('state', '=', 'reserved')])
        if self.starting_at:
            start_time_new = datetime.strptime(
                self.starting_at, "%H:%M").time()
            for rec in reserved:
                start_at = datetime.strptime(rec.starting_at, "%H:%M").time()
                end_at = datetime.strptime(rec.ending_at, "%H:%M").time()
                if start_at <= start_time_new <= end_at:
                    for table in rec.booked_tables_ids:
                        table_inbetween.append(table.id)
        table_floor = [rec.id for rec in tables if
                       rec.id not in table_inbetween]
        domain = [('id', 'in', table_floor)]
        return {'domain': {'booked_tables_ids': domain}}

    @api.depends("booked_tables_ids")
    def _compute_booking_amount(self):
        """ For computing the booking amount """
        payment = self.env['ir.config_parameter'].sudo().get_param(
            "table_reservation_on_website.reservation_charge")
        if payment:
            if self.booked_tables_ids:
                sum_amount = [rec.rate for rec in self.booked_tables_ids]
                self.booking_amount = sum(sum_amount)
            else:
                self.booking_amount = 0
        else:
            self.booking_amount = 0

    def action_cancel(self):
        """ To cancel booking """
        self.write({
            'state': 'cancel'
        })

    def action_reserved(self):
        """ To reserve booking """
        self.write({
            'state': "reserved"
        })

    def action_done(self):
        """ Change state into done """
        self.write({
            'state': 'done'
        })

    def table_reservations(self):
        """ To show reservations in pos product screen """
        today = date.today()
        reservations = self.search_read([('date', '>=', today),
                                         ('state', '=', 'reserved')])
        return reservations

    @api.model
    def edit_reservations(self, booking_id, date, customer, start_time,
                          end_time, floor, table_ids, lead, order_name=None):
        """ For editing reservations from pos """
        time_float = 0
        is_lead_time = self.env['ir.config_parameter'].sudo().get_param(
            "table_reservation_on_website.is_lead_time")
        default_lead_time = self.env['ir.config_parameter'].sudo().get_param(
            "table_reservation_on_website.reservation_lead_time")
        if is_lead_time:
            if lead:
                if isinstance(lead, str):
                    hours, minutes = map(int, lead.split(':'))
                    time_float = hours + minutes / 100.0
                else:
                    time_float = lead
            else:
                time_float = default_lead_time
        if isinstance(table_ids, str):
            table_ids_list = [int(rec) for rec in table_ids.split(',')]
        else:
            table_ids_list = table_ids
        reservation = self.browse(booking_id)
        customer_id = self.env['res.partner'].browse(int(customer))
        floor_id = self.env['restaurant.floor'].browse(floor)
        reservation.update({
            'lead_time': time_float,
            'date': datetime.strptime(date, "%Y-%m-%d"),
            'customer_id': customer_id.id,
            'starting_at': start_time,
            'order_name': order_name,
            'ending_at': end_time,
            'floor_id': floor_id.id,
            'booked_tables_ids': [(6, 0, [rec for rec in table_ids_list])],
        })
        product_id = self.env.ref(
            'table_reservation_on_website.'
            'product_product_table_booking_pos')
        return product_id.id

    @api.model
    def get_table_details(self, floor_id, date, start_time, end_time,
                          booked_table_id=None):
        """ To get un-reserved table details """
        table_inbetween = []
        tables = self.env['restaurant.table'].sudo().search(
            [('floor_id', '=', int(floor_id))])
        reservations = self.env['table.reservation'].sudo().search(
            [('floor_id', '=', int(floor_id)), (
                'date', '=', datetime.strptime(date, "%Y-%m-%d")),
             ('state', '=', 'reserved')])
        start_time = datetime.strptime(start_time, "%H:%M").time()
        end_time = datetime.strptime(end_time, "%H:%M").time()
        if reservations:
            for rec in reservations:
                starting_time = datetime.strptime(
                    rec.starting_at, "%H:%M")
                reservation_start = starting_time - timedelta(
                    hours=int(rec.lead_time),
                    minutes=int((rec.lead_time % 1) * 100))
                reservation_end = datetime.strptime(rec.ending_at,
                                                    "%H:%M").time()
                if reservation_start.time() <= start_time <= reservation_end or reservation_start.time() <= end_time < reservation_end:
                    for table in rec.booked_tables_ids:
                        table_inbetween.append(table.id)
                elif start_time <= reservation_start.time() <= end_time or start_time <= reservation_end < end_time:
                    for table in rec.booked_tables_ids:
                        table_inbetween.append(table.id)
        data_tables = []
        for rec in tables:
            if rec.id not in table_inbetween:
                data_tables.append({
                    'id': rec.id,
                    'name': rec.name
                })
        if booked_table_id:
            for id in booked_table_id:
                if self.env['restaurant.table'].browse(id).floor_id.id == int(
                        floor_id):
                    data_tables.append({
                        'id': id,
                        'name': self.env['restaurant.table'].browse(id).name
                    })
        return data_tables

    @api.model
    def get_reservation_amount(self, table_id=None):
        """ For fetching the reservation amount details of tables """
        amount = 0
        if table_id:
            payment = self.env['ir.config_parameter'].sudo().get_param(
                "table_reservation_on_website.reservation_charge")
            table_id_list = [int(num) for num in table_id.split(',')]
            tables = self.env['restaurant.table'].search([
                ('id', 'in', table_id_list)
            ])
            if payment and table_id:
                if table_id:
                    sum_amount = [rec.rate for rec in tables]
                    amount = sum(sum_amount)
            else:
                amount = amount
            return amount
        return amount

    @api.model
    def create_table_reservation(self, table_id, date, start_time, end_time,
                                 partner, lead_time, floor_id, order_name=None):
        """ For pos table booking """
        time_float = 0
        table_id_list = [int(num) for num in table_id.split(',')]
        is_lead_time = self.env['ir.config_parameter'].sudo().get_param(
            "table_reservation_on_website.is_lead_time")
        default_lead_time = self.env['ir.config_parameter'].sudo().get_param(
            "table_reservation_on_website.reservation_lead_time")
        if is_lead_time:
            if lead_time:
                hours, minutes = map(int, lead_time.split(':'))
                time_float = hours + minutes / 100.0
            else:
                time_float = default_lead_time
        else:
            time_float = time_float
        partner_id = self.env['res.partner'].browse(int(partner))
        self.env['table.reservation'].create({
            'customer_id': partner_id.id,
            'floor_id': floor_id,
            'booked_tables_ids': [(6, 0, [rec for rec in table_id_list])],
            'date': date,
            'starting_at': start_time,
            'ending_at': end_time,
            'state': 'reserved',
            'type': 'pos',
            'lead_time': time_float,
            'order_name': order_name,
        })
        product_id = self.env.ref(
            'table_reservation_on_website.'
            'product_product_table_booking_pos')
        return product_id.id

    @api.model
    def get_avail_table(self, floor_id, date, start_time, end_time, table_ids):
        """To check if table is available while editing reservations from pos"""
        table_ids_list = []
        available = True
        if table_ids and isinstance(table_ids, str):
            table_ids_list = [int(rec) for rec in table_ids.split(',')]
        reservations = self.env['table.reservation'].search([
            ('floor_id', '=', int(floor_id)),
            ('date', '=', datetime.strptime(date, "%Y-%m-%d")),
            ('booked_tables_ids', 'in', table_ids_list),
            ('state', '=', 'reserved')
        ])
        start_time = datetime.strptime(start_time, "%H:%M").time()
        end_time = datetime.strptime(end_time, "%H:%M").time()
        if reservations:
            for rec in reservations:
                starting_time = datetime.strptime(
                    rec.starting_at, "%H:%M")
                reservation_start = starting_time - timedelta(
                    hours=int(rec.lead_time),
                    minutes=int((rec.lead_time % 1) * 100))
                reservation_end = datetime.strptime(rec.ending_at,
                                                    "%H:%M").time()
                if reservation_start.time() <= start_time <= reservation_end:
                    available = False
                elif start_time <= reservation_start.time() <= end_time:
                    available = False
        return available

    @api.model
    def cancel_reservations(self, res_id):
        """ Cancel reservations from pos screen """
        res = self.browse(int(res_id))
        res.update({
            'state': 'cancel'
        })
