# -*- coding: utf-8 -*-
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
"""
This module defines the Fleet Rental Order model.
"""
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class FleetRentalOrder(models.Model):
    """Car Rental Booking."""
    _name = 'fleet.rental.order'
    _description = 'Car Rental Booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Booking Reference', required=True, copy=False, readonly=True,
        index=True, default=lambda self: 'New', help='Booking reference number.')
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('picked_up', 'Picked Up'),
            ('returned', 'Returned'),
            ('cancelled', 'Cancelled')
        ],
        string='Status',
        readonly=True,
        copy=False,
        index=True,
        tracking=3,
        default='draft',
        help='Current state of the booking.'
    )
    vehicle_id = fields.Many2one(
        'fleet.vehicle', string='Vehicle', required=True,
        tracking=1, help='Rented vehicle.')
    pickup_datetime = fields.Datetime(string='Pickup Time', required=True,
                                      tracking=2, help='Scheduled pickup time.')
    return_datetime = fields.Datetime(string='Return Time', required=True,
                                      tracking=2, help='Scheduled return time.')
    pickup_location_id = fields.Many2one(
        'fleet.rental.location', string='Pickup Location',
        required=True, help='Location for pickup.')
    return_location_id = fields.Many2one(
        'fleet.rental.location', string='Return Location',
        required=True, help='Location for return.')
    driver_name = fields.Char(string='Driver Name', required=True,
                              help='Name of the driver.')
    driver_email = fields.Char(string='Driver Email', required=True,
                               help='Email of the driver.')
    driver_phone = fields.Char(string='Driver Phone', required=True,
                               help='Phone number of the driver.')
    driver_license = fields.Char(string='License Number', help='Driver license number.')
    driver_age = fields.Integer(string='Driver Age', help='Age of the driver.')
    currency_id = fields.Many2one(
        'res.currency', string="Currency", default=lambda self: self.env.company.currency_id,
        readonly=True, help='Currency for the booking.')
    insurance_id = fields.Many2one(
        'fleet.rental.insurance', string='Insurance Plan',
        help='Selected insurance plan.')
    addon_ids = fields.Many2many('fleet.rental.addon',
                                 string='Add-ons', help='Selected add-ons.')
    amount_base = fields.Float(string='Base Rate', tracking=True, help='Base rental rate.')
    amount_insurance = fields.Float(string='Insurance Cost', tracking=True, help='Cost of insurance.')
    amount_addons = fields.Float(string='Add-ons Cost', tracking=True, help='Cost of add-ons.')
    amount_total = fields.Float(string='Total Amount', compute='_compute_amount_total',
                                store=True, tracking=True, help='Total cost of the booking.')

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to assign sequence."""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('fleet.rental.order') or 'New'
        return super().create(vals_list)

    @api.depends('amount_base', 'amount_insurance', 'amount_addons')
    def _compute_amount_total(self):
        """Compute the total amount."""
        for order in self:
            order.amount_total = order.amount_base + order.amount_insurance + order.amount_addons

    @api.constrains('vehicle_id', 'pickup_datetime', 'return_datetime', 'state')
    def _check_overlap(self):
        """Check for overlapping bookings."""
        for order in self:
            if order.state in ['confirmed', 'picked_up']:
                overlapping = self.search([
                    ('id', '!=', order.id),
                    ('vehicle_id', '=', order.vehicle_id.id),
                    ('state', 'in', ['confirmed', 'picked_up']),
                    ('pickup_datetime', '<', order.return_datetime),
                    ('return_datetime', '>', order.pickup_datetime),
                ])
                if overlapping:
                    raise ValidationError("This vehicle is already booked for the selected dates.")

    def action_confirm(self):
        """Confirm the booking."""
        self.write({'state': 'confirmed'})
        
    def action_pickup(self):
        """Mark the vehicle as picked up."""
        self.write({'state': 'picked_up'})
        
    def action_return(self):
        """Mark the vehicle as returned."""
        self.write({'state': 'returned'})
        
    def action_cancel(self):
        """Cancel the booking."""
        self.write({'state': 'cancelled'})
