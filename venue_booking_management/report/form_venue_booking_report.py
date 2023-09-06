# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Risvana AR (odoo@cybrosys.com)
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
###############################################################################
import pytz
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class VenueBookingReport(models.AbstractModel):
    """Class is used to print pdf report for the venue_booking module form view"""
    _name = 'report.venue_booking_management.report_venue_booking'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Function to return values for the report,
        docids: it will provide the current id the model"""
        current = fields.datetime.now().astimezone(
            pytz.timezone(self.env.user.tz))
        current = current.strftime("%d-%m-%Y %H:%M:%S")
        if docids:
            doc_ids = self.env['venue.booking'].sudo().browse(docids)
            return {
                'doc_ids': doc_ids,
                'today_date': current,
            }
        else:
            form_data = data['form']
            # Initialize the SQL WHERE clause
            where = '1=1'
            # Check if the start_date is greater than end_date
            if form_data['start_date'] and form_data['end_date'] and form_data[
                'start_date'] > form_data['end_date']:
                raise ValidationError('Start Date must be less than End Date')
            # Add conditions to the WHERE clause based on form data
            if form_data["partner_id"]:
                where += """ AND tb.partner_id = %s""" % form_data['partner_id'][0]
            if form_data['start_date']:
                where += """ AND tb.date >= '%s'""" % form_data['start_date']
            if form_data['end_date']:
                where += """ AND tb.date <= '%s'""" % form_data['end_date']
            if form_data['venue_id']:
                where += """ AND tb.venue_id = %s""" % form_data['venue_id'][0]
            # Execute the SQL query with the WHERE clause
            self.env.cr.execute("""
                        SELECT tb.ref, pr.name, fv.name as venue, tb.booking_type,
                        tb.date, tb.start_date, tb.end_date, tb.state
                        FROM venue_booking as tb
                        INNER JOIN res_partner as pr ON pr.id = tb.partner_id
                        INNER JOIN venue as fv ON fv.id = tb.venue_id
                        WHERE %s
                    """ % where)
            # Fetch the query results
            rec = self.env.cr.dictfetchall()
            # Return the data for the report
            return {
                'docs': rec,
                'docs2': form_data,
                'today_date': current,
            }
