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
from odoo import api, models, _
from odoo.exceptions import ValidationError


class TruckBookingReport(models.AbstractModel):
    """Class to return values for the truck booking report"""
    _name = 'report.packers_and_movers_management.report_truck_booking'

    @api.model
    def _get_report_values(self, docids, data=None):
        report = []
        docs = self.env['truck.booking']

        booking_ids = data.get('booking_ids') if data else False
        if booking_ids:
            docs = self.env['truck.booking'].browse(booking_ids)
        elif data and data.get('report'):
            report = data.get('report')
        elif docids:
            docs = self.env['truck.booking'].browse(docids)

        if docs and not report:
            report = []
            for doc in docs:
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

        if not docs and not report:
            raise ValidationError(self.env._("No booking data found for the selected criteria."))

        return {
            'doc_ids': docids,
            'docs': docs,
            'report': report,
        }
