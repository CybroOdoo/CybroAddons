# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vyshnav AR(<https://www.cybrosys.com>)
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
from odoo import api, fields, models, _


class VehicleRental(models.Model):
    """This model represents details about vehicle rentals within the
    context of agriculture management. It provides a structured way to manage
    information related to renting vehicles for agricultural tasks."""
    _name = 'vehicle.rental'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Vehicle Rental Details'
    _rec_name = 'vehicle_id'

    name = fields.Char(string='Reference', readonly=True,
                       default=lambda self: _('New'), copy=False,
                       help='Field for the sequence of renting entries of '
                            'vehicles.')
    farmer_id = fields.Many2one('farmer.detail', string='Farmer',
                                help='Select the farmer who needs vehicle.',
                                required=True, tracking=True)
    vehicle_id = fields.Many2one('vehicle.detail',
                                 help="Select the vehicle that used for farming",
                                 string='Vehicle', required=True, tracking=True)
    no_of_days = fields.Float(string='No of Days',
                              compute='_compute_no_of_days',
                              help="The number of days we want to rent that "
                                   "vehicle.", tracking=True, store=True)
    start_date = fields.Date(string='Start Date', tracking=True,
                             help=" Start date of rental period", required=True)
    end_date = fields.Date(string='End Date', help="End date of rental period",
                           required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 help='The company associated with the current '
                                      'user or environment.',
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id',
                                  string='Currency', help='Currency of company')
    amount = fields.Monetary(string='Amount', help="Rental amount per day",
                             required=True)
    total_amount = fields.Monetary(string='Total Amount',
                                   help="Total rental amount",
                                   compute='_compute_total_amount',
                                   currency_field='currency_id')
    note = fields.Text(string='Description', tracking=True,
                       help="Please describe any additional details here if "
                            "there is a need to mention additional data.")
    state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirmed'), ('return', 'Returned'),
         ('paid', 'Paid'), ('cancel', 'Cancel')], string='Status',
        default='draft', tracking=True, copy=False,
        help="Status of renting the vehicle, Which is th status of the vehicle "
             "rented?")
    vehicle_paid_bool = fields.Boolean(string='Paid Bool', default=False,
                                       copy=False)

    @api.model
    def create(self, values):
        """Function for creating new animal rental"""
        if values.get('name', _('New')) == _('New'):
            values['name'] = self.env['ir.sequence'].next_by_code(
                'vehicle.rental') or _('New')
        res = super(VehicleRental, self).create(values)
        return res

    @api.depends('no_of_days', 'amount')
    def _compute_total_amount(self):
        """ Function for compute total amount """
        for record in self:
            record.total_amount = record.no_of_days * record.amount

    @api.depends('start_date', 'end_date')
    def _compute_no_of_days(self):
        """Function for calculating the rental period based start date and
        end date"""
        for record in self:
            if record.start_date and record.end_date:
                days = (record.end_date - record.start_date).days
                record.no_of_days = days

    def action_draft(self):
        """ Function for change state of animal rental to draft """
        self.state = 'draft'

    def action_confirm(self):
        """ Function for change state of crop request to confirm """
        self.state = 'confirm'

    def action_return(self):
        """ Function for change state of crop request to cancel """
        self.state = 'return'

    def action_cancel(self):
        """ Function for change state of crop request to cancel """
        self.state = 'cancel'

    def action_register_payment(self):
        """Method for viewing the wizard for register payment"""
        view_id = self.env.ref(
            'agriculture_management_odoo.vehicle_register_payment_wizard_view_form').id
        return {
            'name': 'Register Payment',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'vehicle.register.payment.wizard',
            'views': [(view_id, 'form')],
            'context': {
                'default_farmer_id': self.farmer_id.id,
                'default_rental_duration': self.no_of_days,
                'default_amount': self.total_amount,
                'default_ref': self.name
            },
            'target': 'new',
        }
