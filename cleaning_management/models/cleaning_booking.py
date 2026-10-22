# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Safa KB (odoo@cybrosys.com)
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
from datetime import date
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CleaningBooking(models.Model):
    """Create a new model for booking purposes.
    The system will incorporate three buttons to indicate the
    booking and cleaning status: "Confirm", "Clean" and "Cancel"."""
    _name = "cleaning.booking"
    _description = "Cleaning Booking"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'customer_name_id'

    def _default_cleaning_team_ids(self):
        """Returns default values for cleaning_team_ids records"""
        return self.env['cleaning.team'].search([]).ids  # pylint: disable=no-search-all

    customer_name_id = fields.Many2one('res.partner',
                                       string='Name of Customer',
                                       required=True,
                                       help="Choose customer name")
    address = fields.Char(required=True,
                          help="Enter address of customer")
    building_type_id = fields.Many2one('building.type',
                                       required=True,
                                       help="Choose building type")
    booking_date = fields.Date(default=fields.Date.today,
                               help="Choose the booking date")
    cleaning_team_ids = fields.Many2many('cleaning.team',
                                         help="Store cleaning team based on "
                                              "cleaning_time",
                                         default=lambda self: self._default_cleaning_team_ids())
    cleaning_team_id = fields.Many2one('cleaning.team',
                                       help="Choose cleaning team",
                                       required=True,
                                       domain="[('id', 'in', "
                                              "cleaning_team_ids)]")
    cleaning_inspection_id = fields.Many2one('cleaning.inspection',
                                             help="Choose Cleaning Inspection")
    cleaning_team_duty_id = fields.Many2one('cleaning.team.duty',
                                            help="Choose Cleaning Team Duty")
    cleaning_date = fields.Date(required=True,
                                help="Choose Date for cleaning")
    cleaning_time = fields.Selection([('morning', 'Morning'),
                                      ('evening', 'Evening'),
                                      ('night', 'Night')],
                                     help="Choose Time for cleaning",
                                     required=True)
    description = fields.Char(help="Enter Description For Booking")
    duration = fields.Selection([('forever', 'Forever'),
                                 ('fixed', 'Fixed')],
                                default='forever', help="Choose Duration For Cleaning")
    end_after = fields.Integer(help="Choose End of cleaning management")
    end_duration = fields.Selection([('months', 'Months'),
                                     ('years', 'Years')],
                                    help="Choose End duration of booking")
    cleaning_shift_id = fields.Many2one("cleaning.shift",
                                        help="Cleaning Shift",
                                        string="Choose Cleaning Shift")
    self_closable = fields.Boolean(string='Is Self Closable',
                                   help="When checked, reservations will be automatically closed.")
    automatic_closing = fields.Integer(help="Automatic Closing Chooser")
    location_state_id = fields.Many2one('res.country.state',
                                        string="State",
                                        required=True,
                                        help="Choose State For Cleaning")
    place = fields.Char(help="Enter Place of Customer")
    state = fields.Selection([('draft', 'Draft'),
                              ('booked', 'Booked'),
                              ('cleaned', 'Cleaned'),
                              ('cancelled', 'Cancelled')],
                             default='draft', string='Status',
                             help="Stages For Cleaning Processes",
                             tracking=True)
    confirm_stage = fields.Boolean(string="Is Confirm", default=True,
                                   help="When checked, the status will be 'Confirm'.")
    clean_stage = fields.Boolean(string="Clean", default=True,
                                 help="When checked, the status will be 'Clean'.")
    cancel_stage = fields.Boolean(string="Cancel", default=True,
                                  help="When checked, the status will be 'Cancel'.")
    unit_price = fields.Float(default=0.0, required=True,
                              help="Unit price per hour")
    total_hour_of_working = fields.Char(string="Total working hours",
                                        help="Total working hours done by Team")
    invoice_count = fields.Integer(compute="_compute_invoice_count")

    @api.onchange('cleaning_time')
    def _onchange_cleaning_time(self):
        """The team leader will appear at the scheduled cleaning time."""
        if self.cleaning_time:
            domain = [('duty_type', '=', self.cleaning_time)]
            busy_duties = self.env['cleaning.team.duty'].search([
                ('cleaning_date', '=', self.cleaning_date),
                ('cleaning_time', '=', self.cleaning_time),
                ('state', 'not in', ['cancelled', 'cleaned'])])
            if busy_duties:
                domain.append(('id', 'not in', busy_duties.team_id.ids))
            self.cleaning_team_ids = self.env['cleaning.team'].search(domain)

    @api.onchange('cleaning_team_id')
    def _onchange_cleaning_team_id(self):
        """The team leader's time will appear when changing the leader."""
        self.cleaning_time = self.cleaning_team_id.duty_type

    def action_booking(self):
        """The button action for "Confirm" typically involves
        finalizing and saving the booking details entered
        by the user."""
        for rec in self:
            cleaning_team_duty = rec.cleaning_team_duty_id.create({
                "team_id": rec.cleaning_team_id.id,
                "team_leader_id": rec.cleaning_team_id.team_leader_id.employee_name_id.id,
                "members_ids": rec.cleaning_team_id.members_ids.employee_name_id.ids,
                "location_state_id": rec.location_state_id.id,
                "place": rec.place,
                "customer_id": rec.customer_name_id.id,
                "cleaning_date": rec.cleaning_date,
                "cleaning_time": rec.cleaning_time,
                "cleaning_id": rec.id
            })
            rec.write(
                {'state': 'booked', 'confirm_stage': False,
                 'clean_stage': False,
                 'cancel_stage': False,
                 'cleaning_team_duty_id': cleaning_team_duty.id})

    def action_cancel(self):
        """The button action for "Cancel" typically involves canceling
         and removing a booking that was previously confirmed or reserved."""
        for rec in self:
            rec.cleaning_team_duty_id.write({'state': 'cancelled'})
            rec.write(
                {'state': 'cancelled', 'confirm_stage': False,
                 'cancel_stage': True,
                 'clean_stage': True})

    def action_create_invoice(self):
        """Function for create an invoice for cleaning processes"""
        for rec in self:
            if rec.unit_price > 0.0:
                invoice = rec.env['account.move'].create({
                    'move_type': 'out_invoice',
                    'partner_id': rec.customer_name_id.id,
                    'invoice_date': date.today(),
                    'payment_reference': rec.cleaning_date,
                    'cleaning_id': rec.id,
                    'invoice_line_ids': [(0, 0, {
                        'name': f"{rec.cleaning_team_id.name} ({rec.cleaning_inspection_id.inspection_date_and_time})",
                        'price_unit': float(rec.unit_price) * float(
                            rec.total_hour_of_working),
                    })],
                })
                return {
                    'name': 'account.move.form',
                    'res_model': 'account.move',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'view_id': rec.env.ref("account.view_move_form").id,
                    'res_id': invoice.id,
                    'target': 'current'
                }
            else:
                raise ValidationError(
                    self.env._("Specify the unit price per hour"))

    def action_view_invoice(self):
        """Function for open Invoice Smart Button"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice',
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'domain': [('cleaning_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def _compute_invoice_count(self):
        """Function for count number of Invoices"""
        counts = dict(self.env['account.move']._read_group(
            [('cleaning_id', 'in', self.ids)], ['cleaning_id'], ['__count']))
        for record in self:
            record.invoice_count = counts.get(record, 0)