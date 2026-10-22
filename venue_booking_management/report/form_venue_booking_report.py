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
import pytz

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class VenueBookingReport(models.AbstractModel):
    """Class is used to print pdf report for the venue_booking module
    form view"""
    _name = 'report.venue_booking_management.report_venue_booking'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Function to return values for the report,
        docids: it will provide the current id the model"""
        user_tz = self.env.user.tz or 'UTC'
        current = fields.Datetime.now().astimezone(pytz.timezone(user_tz))
        current = current.strftime("%d-%m-%Y %H:%M:%S")
        if docids:
            doc_ids = self.env['venue.booking'].browse(docids)
            return {
                'doc_ids': doc_ids,
                'today_date': current,
            }
        form_data = data.get('form', {}) if data else {}
        # Check if the start_date is greater than end_date
        if form_data.get('start_date') and form_data.get('end_date') and form_data[
            'start_date'] > form_data['end_date']:
            raise ValidationError(self.env._('Start Date must be less than End Date'))
        # Add conditions to the WHERE clause based on form data with parameterized query
        where_clauses = ['1=1']
        params = []
        if form_data.get("partner_id"):
            where_clauses.append("tb.partner_id = %s")
            params.append(form_data['partner_id'][0])
        if form_data.get('start_date'):
            where_clauses.append("tb.date >= %s")
            params.append(form_data['start_date'])
        if form_data.get('end_date'):
            where_clauses.append("tb.date <= %s")
            params.append(form_data['end_date'])
        if form_data.get('venue_id'):
            where_clauses.append("tb.venue_id = %s")
            params.append(form_data['venue_id'][0])
        where_sql = " AND ".join(where_clauses)
        # Execute the parameterized SQL query
        self.env.cr.execute(f"""
                    SELECT tb.ref, pr.name, fv.name as venue, tb.booking_type,
                    tb.date, tb.start_date, tb.end_date, tb.state
                    FROM venue_booking as tb
                    INNER JOIN res_partner as pr ON pr.id = tb.partner_id
                    INNER JOIN venue as fv ON fv.id = tb.venue_id
                    WHERE {where_sql}
                """, tuple(params))
        # Fetch the query results
        rec = self.env.cr.dictfetchall()
        # Return the data for the report
        return {
            'docs': rec,
            'docs2': form_data,
            'today_date': current,
        }
