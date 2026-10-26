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


class TruckFormReport(models.AbstractModel):
    """Class is used to print pdf report for the truck_booking module form
    view"""
    _name = 'report.packers_and_movers_management.form_truck_booking_report'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not docids and data and data.get('booking_ids'):
            docids = data.get('booking_ids')
        if not docids:
            raise ValidationError(self.env._("No booking record found to print."))
        docs = self.env['truck.booking'].browse(docids)
        if not docs:
            raise ValidationError(self.env._("No booking data found to print."))

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

        return {
            'doc_ids': docids,
            'docs': docs,
            'report': report,
        }
