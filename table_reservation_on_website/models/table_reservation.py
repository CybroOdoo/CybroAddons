# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fathima Mazlin AM (odoo@cybrosys.com)
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
#############################################################################
from datetime import datetime
import re
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class TableReservation(models.Model):
    """Create new model table reservation"""
    _name = "table.reservation"
    _description = 'Table Reservation'
    _rec_name = 'sequence'

    sequence = fields.Char(string='Sequence', default=_('New'), readonly=True,
                           copy=False, help="Sequence number for records")
    customer_id = fields.Many2one(comodel_name="res.partner",
                                  string="Customer", help="Name of the "
                                                          "customer",
                                  required=True)
    floor_id = fields.Many2one(comodel_name='restaurant.floor', string="Floor "
                                                                       "Plan",
                               help="Booked floor", required=True)
    booked_tables_ids = fields.Many2many(comodel_name='restaurant.table',
                                         string="Tables", required=True,
                                         help="Booked tables")
    date = fields.Date(string="Date", help="Date of reservation",
                       required=True)
    starting_at = fields.Char(string="Starting At", help="starting time of "
                                                         "reservation",
                              required=True)
    ending_at = fields.Char(string="Ending At", help="Ending time of "
                                                     "reservation",
                            required=True)
    booking_amount = fields.Float(string="Booking Charge", help="Amount for "
                                                                "booking",
                                  compute="_compute_booking_amount")
    state = fields.Selection([('draft', "Draft"), ('reserved', 'Reserved'),
                              ('done', "Done"), ("cancel", "Cancelled")],
                             default='draft', string="Status",
                             help="State for records")

    @api.model
    def create(self, vals):
        """Super create function to add sequence number"""
        vals['sequence'] = self.env['ir.sequence'].next_by_code(
            "table.reservation")
        return super(TableReservation, self).create(vals)

    @api.onchange('starting_at', 'ending_at')
    def _constrains_time(self):
        """Pattern for time"""
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
    def _onchange_floor(self):
        """To show the tables corresponding the floor"""
        tables = self.env['restaurant.table'].search([('floor_id', '=',
                                                       self.floor_id.id)])
        table_inbetween = []
        reserved = self.search([('floor_id', '=', self.floor_id.id), ('date',
                                                                     '=',
                                                                   self.date),
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
        """For computing the booking amount"""
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
        """For cancel button"""
        self.write({
            'state': 'cancel'
        })

    def action_reserved(self):
        """For reserved button"""
        self.write({
            'state': "reserved"
        })

    def action_done(self):
        """For done button"""
        self.write({
            'state': 'done'
        })
