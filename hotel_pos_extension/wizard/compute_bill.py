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
from odoo import api, fields, models

class ComputeBillWizard(models.TransientModel):
    """
    Wizard model used to generate and manage billing details
    for room bookings, services, food orders, fleet, events,
    and related POS orders.
    """
    _name = 'compute.bill'
    _description = 'Compute Bill Wizard'

    booking_id = fields.Many2one('room.booking', string='Booking', required=True, help='Room booking record for which to compute the bill.')
    partner_id = fields.Many2one('res.partner', related='booking_id.partner_id', string='Customer', help='Customer linked to the selected room booking.')
    currency_id = fields.Many2one('res.currency', related='booking_id.currency_id', help='Currency of the room booking.')
    
    # Folio Lines (Room, Food, Service, Fleet, Event)
    room_line_ids = fields.Many2many('room.booking.line', string='Room Lines', compute='_compute_folio_lines', help='Room booking lines included in the bill.')
    food_line_ids = fields.Many2many('food.booking.line', string='Food Lines', compute='_compute_folio_lines', help='Food order lines included in the bill.')
    service_line_ids = fields.Many2many('service.booking.line', string='Service Lines', compute='_compute_folio_lines', help='Service booking lines included in the bill.')
    fleet_line_ids = fields.Many2many('fleet.booking.line', string='Fleet Lines', compute='_compute_folio_lines', help='Vehicle/Fleet booking lines included in the bill.')
    event_line_ids = fields.Many2many('event.booking.line', string='Event Lines', compute='_compute_folio_lines', help='Event booking lines included in the bill.')
    
    pos_order_ids = fields.Many2many('pos.order', string='POS Orders', compute='_compute_orders', store=True, readonly=False, help='POS orders associated with this booking to include in the bill.')
    bill_type = fields.Selection([
        ('combined', 'Combined Bill'),
        ('isolate', 'Isolate Bill')
    ], string='Print Bill', default='combined', required=True, help='Select whether to print a combined bill or an isolated bill.'

)

    @api.depends('booking_id')
    def _compute_folio_lines(self):
        """
        Compute and assign room, food, service, fleet, and event lines
        from the selected booking record to the wizard.
        """
        for wizard in self:
            if wizard.booking_id:
                wizard.room_line_ids = wizard.booking_id.room_line_ids
                wizard.food_line_ids = wizard.booking_id.food_order_line_ids
                wizard.service_line_ids = wizard.booking_id.service_line_ids
                wizard.fleet_line_ids = wizard.booking_id.vehicle_line_ids
                wizard.event_line_ids = wizard.booking_id.event_line_ids
            else:
                wizard.room_line_ids = wizard.food_line_ids = wizard.service_line_ids = wizard.fleet_line_ids = wizard.event_line_ids = False

    @api.depends('booking_id')
    def _compute_orders(self):
        """
        Compute and fetch POS orders linked with the selected booking
        and assign them to the wizard record.
        """
        for wizard in self:
            if wizard.booking_id and 'booking_id' in self.env['pos.order']._fields:
                pos_orders = self.env['pos.order'].search([
                    ('booking_id', '=', wizard.booking_id.id)
                ])
                wizard.pos_order_ids = pos_orders
            else:
                wizard.pos_order_ids = False

    def action_print_bill(self):
        """Method to print the bill report"""
        self.ensure_one()
        # No 'data' argument to ensure 'docs' is populated with the wizard record
        return self.env.ref('hotel_pos_extension.action_report_combined_bill').report_action(self)
