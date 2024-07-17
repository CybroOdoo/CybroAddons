# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anfas Faisal K (odoo@cybrosys.com)
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
from odoo import fields, models


class TruckBookingMake(models.TransientModel):
    """Wizard to print pdf report of booking"""
    _name = 'make.truck.booking.pdf'
    _description = "Truck Booking PDF"

    from_date = fields.Date(string='From Date', help='Add the start date')
    to_date = fields.Date(string='To Date', help='Add the end date')
    truck_id = fields.Many2one('fleet.vehicle.model', string='Track Type',
                               domain=[('vehicle_type', '=', 'truck')],
                               help='Select the truck type')
    goods_type_id = fields.Many2one('goods.type', string='Goods Type',
                                    help='Select the goods type')
    partner_id = fields.Many2one('res.partner', string='Customer',
                                 required=True,
                                 help='Select the customer')

    def action_report_truck_booking(self):
        """Function to print PDF report"""
        query = """select pr.name,fv.name as truck,gt.name as goods,tb.from_location,tb.to_location,tb.distance,
                tb.weight,tb.unit,amount,tb.date,tb.state from truck_booking as tb
                inner join res_partner as pr on pr.id = tb.partner_id
                inner join fleet_vehicle_model as fv on fv.id = tb.truck_id
                inner join goods_type as gt on gt.id = tb.goods_type_id
                where pr.id = %d """ % self.partner_id.id
        if self.truck_id:
            query += """ and fv.id = %d """ % self.truck_id.id
        if self.goods_type_id:
            query += """ and gt.id = %d """ % self.goods_type_id.id
        if self.from_date:
            query += """ and tb.date >= '%s' """ % self.from_date
        if self.to_date:
            query += """ and tb.date <= '%s' """ % self.to_date
        self.env.cr.execute(query)
        report = self.env.cr.dictfetchall()
        data = {'date': self.read()[0],'report': report}
        return self.env.ref('packers_and_movers_management.action_report_booking').report_action(None, data=data)
