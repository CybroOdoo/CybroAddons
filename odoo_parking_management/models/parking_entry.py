# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#   This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import datetime
from odoo import api, fields, models, _


class ParkingEntry(models.Model):
    """Details about the Parking"""
    _name = 'parking.entry'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Public Park Entry'

    name = fields.Char(string='Reference', readonly=True,
                       default=lambda self: _('New'),
                       help='Field for the sequence of parking entries')
    partner_id = fields.Many2one('res.partner', string='Contact',
                                 tracking=True, help='Field for customer')
    mobile = fields.Char(related='partner_id.phone', string='Mobile',
                         store=True, readonly=False,
                         help='Mobile number of customer')
    email = fields.Char(related='partner_id.email', string='Email',
                        store=True, readonly=False,
                        help='E-mail of customer')
    check_in = fields.Datetime(string='Check In', readonly=True,
                               tracking=True, help='Check In time of the '
                                                   'vehicle for parking')
    vehicle_id = fields.Many2one('vehicle.details', string='Vehicle',
                                 tracking=True, required=True,
                                 help='Vehicle of Customer')
    vehicle_number = fields.Char(related='vehicle_id.number_plate',
                                 string='Vehicle Number', store=True,
                                 readonly=False, tracking=True,
                                 help='Vehicle number of customer')
    slot_type_id = fields.Many2one('slot.type', string='Slot Type',
                                   tracking=True, required=True,
                                   help='Slot type fr the vehicle')
    slot_id = fields.Many2one('slot.details', string='Slot', tracking=True,
                              required=True,
                              help='Slot assigned for vehicle of Customer')
    user_id = fields.Many2one('res.users', string='Created By',
                              default=lambda self: self.env.user,
                              tracking=True,
                              help='Field for user that entries are created')
    created_date = fields.Datetime(string='Created Datetime',
                                   default=lambda self: fields.Datetime.now(),
                                   tracking=True,
                                   help='Date which entry was created')
    check_out = fields.Datetime(string='Check Out', readonly=True,
                                tracking=True, help='Check Out time of vehicle')
    duration = fields.Float(string='Duration', compute='compute_duration',
                            store=True, help='Time spent by the vehicles')
    customer_type = fields.Selection(
        [('private', 'Private'), ('public', 'Public')],
        string='Type', default='public',
        tracking=True, required=True,
        help='Type of the customer')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company,
                                 help='Name of the company')
    location_id = fields.Many2one('location.details', string='Location',
                                  tracking=True, required=True,
                                  help='Name of the location')
    state = fields.Selection([('draft', 'Draft'), ('check_in', 'Check In'),
                              ('check_out', ' Check Out'),
                              ('payment', 'Payment')],
                             string='Status', default='draft', tracking=True,
                             help='status of the vehicle', copy=False)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  related='company_id.currency_id',
                                  default=lambda self:
                                  self.env.user.company_id.currency_id.id,
                                  help='Currency used by the company')
    parking_cost = fields.Monetary(string='Parking Cost', tracking=True,
                                   help='Cost for the parking.')
    check_in_bool = fields.Boolean(string='Check In Bool',
                                   default=False,
                                   copy=False,
                                   help='Check if checked in.')
    check_out_bool = fields.Boolean(string='Check Out Bool',
                                    default=False,
                                    copy=False,
                                    help='Check if checked out.')
    paid_bool = fields.Boolean(string='Paid Bool',
                               default=False,
                               copy=False,
                               help='Check if paid.')

    @api.model
    def create(self, values):
        """Method for generating the sequence for public and private users"""
        res = super(ParkingEntry, self).create(values)
        if res.customer_type == "private":
            res['name'] = self.env['ir.sequence'].next_by_code(
                'private.parking.entry')
        if res.customer_type == 'public':
            res['name'] = self.env['ir.sequence'].next_by_code(
                'public.parking.entry')
        return res

    @api.depends('check_out')
    def compute_duration(self):
        """Method for computing the duration of checking in and checking out
        of vehicles"""
        for rec in self:
            rec.duration = False
            if rec.check_out:
                entry = datetime.datetime.strptime(str(rec.check_in),
                                                   "%Y-%m-%d %H:%M:%S")
                out = datetime.datetime.strptime(str(rec.check_out),
                                                 "%Y-%m-%d %H:%M:%S")
                dur_dif = out - entry
                dur = dur_dif.total_seconds()
                dur_hour = str(datetime.timedelta(seconds=dur))
                vals = dur_hour.split(':')
                t, hours = divmod(float(vals[0]), 24)
                t, minutes = divmod(float(vals[1]), 60)
                minutes = minutes / 60.0
                rec.duration = hours + minutes

    @api.onchange('slot_type_id')
    def onchange_slot_type_id(self):
        """Method for changing the slot type"""
        domain = {'slot_id': [('slot_type_id', '=', self.slot_type_id.id)]}
        return {'domain': domain}

    def action_check_in(self):
        """Method for checking in"""
        self.state = 'check_in'
        self.check_in_bool = True
        self.check_out_bool = False
        self.check_in = fields.Datetime.now()

    def action_check_out(self):
        """Method for checking out"""
        self.state = 'check_out'
        self.check_out_bool = True
        self.check_in_bool = False
        self.check_out = fields.Datetime.now()

    def action_register_payment(self):
        """Method for viewing the wizard for register payment"""
        view_id = self.env.ref('odoo_parking_management.register_payment_wizard_view_form').id
        return {
            'name': 'Register Payment',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'register.payment.wizard',
            'views': [(view_id, 'form')],
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_parking_duration': self.duration,
                'default_amount': self.parking_cost,
                'default_ref': self.name
            },
            'target': 'new',
        }
