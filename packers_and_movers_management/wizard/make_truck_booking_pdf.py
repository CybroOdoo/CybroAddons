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
#############################################################################
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class TruckBookingMake(models.TransientModel):
    """Wizard to print a PDF report of booking"""
    _name = 'make.truck.booking.pdf'
    _description = "Truck Booking PDF"

    from_date = fields.Date(help='Add the start date')
    to_date = fields.Date(help='Add the end date.')
    truck_id = fields.Many2one('fleet.vehicle.model',
                               string='Truck Type',
                               domain=[('vehicle_type', '=', 'truck')],
                               help='Select the truck type.')
    goods_type_id = fields.Many2one('goods.type',
                                    help='Select the goods type.')
    partner_id = fields.Many2one('res.partner', string='Customer',
                                 required=False,
                                 help='Select the customer.')

    def action_report_truck_booking(self):
        """Function to print a PDF report"""
        if self.from_date and self.to_date and self.from_date > self.to_date:
            raise ValidationError(self.env._("From Date cannot be later than To Date."))
        domain = []
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        if self.truck_id:
            domain.append(('truck_id', '=', self.truck_id.id))
        if self.goods_type_id:
            domain.append(('goods_type_id', '=', self.goods_type_id.id))
        if self.from_date:
            domain.append(('date', '>=', self.from_date))
        if self.to_date:
            domain.append(('date', '<=', self.to_date))

        bookings = self.env['truck.booking'].search(domain)
        if not bookings:
            raise ValidationError(self.env._("No booking data found for the selected criteria."))

        report = []
        for doc in bookings:
            report.append({
                'reference_no': doc.reference_no or '',
                'name': doc.partner_id.name or '',
                'truck': doc.truck_id.name or '',
                'goods': doc.goods_type_id.name or '',
                'from_location': doc.from_location or '',
                'to_location': doc.to_location or '',
                'distance': doc.distance or 0.0,
                'weight': doc.weight or 0,
                'unit': doc.unit or '',
                'amount': doc.amount or 0.0,
                'date': str(doc.date) if doc.date else '',
                'state': doc.state or '',
            })

        data = {
            'date': self.read()[0],
            'booking_ids': bookings.ids,
            'report': report,
        }
        return self.env.ref('packers_and_movers_management'
                            '.action_report_booking').report_action(self,
                                                                    data=data)
