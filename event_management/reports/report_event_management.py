# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
################################################################################
import pytz
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ReportHotelManagement(models.AbstractModel):
    """Class for fetch and carry off pdf data to template"""
    _name = "report.event_management.report_event_management"
    _description = "Event Management Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        """Get values for the Event Management report"""

        form_data = data.get('form', {})
        where = '1=1 '

        # ---------------------------
        # Validations
        # ---------------------------
        if form_data.get('date_from') and form_data.get('date_to') and \
                form_data['date_from'] > form_data['date_to']:
            raise ValidationError('From Date must be less than To Date')

        # ---------------------------
        # Dynamic domain conditions
        # ---------------------------
        if form_data.get('partner_id'):
            where += " AND e.partner_id = %s" % form_data['partner_id'][0]

        if form_data.get('date_from'):
            where += " AND e.date >= '%s'" % form_data['date_from']

        if form_data.get('date_to'):
            where += " AND e.date <= '%s'" % form_data['date_to']

        if form_data.get('type_event_ids'):
            event_list = data.get('event_types', [])
            if len(event_list) == 1:
                where += " AND e.type_of_event_id = %s" % event_list[0]
            else:
                where += " AND e.type_of_event_id IN %s" % (tuple(event_list),)

        if form_data.get('event_state'):
            where += " AND e.state = '%s'" % form_data['event_state']

        # ---------------------------
        # Execute SQL
        # ---------------------------
        self.env.cr.execute(f"""
            SELECT
                e.name AS event,
                t.name AS type,
                r.name AS partner,
                e.state,
                e.date,
                e.start_date,
                e.end_date
            FROM event_management e
            INNER JOIN res_partner r ON e.partner_id = r.id
            INNER JOIN event_management_type t ON e.type_of_event_id = t.id
            WHERE {where}
            ORDER BY e.date
        """)

        rec = self.env.cr.dictfetchall()

        # ---------------------------
        # Timezone-aware current datetime
        # ---------------------------
        now_user_tz = fields.Datetime.context_timestamp(
            self.env.user,
            fields.Datetime.now()
        )

        # ---------------------------
        # Return values
        # ---------------------------
        return {
            'docs': rec,
            'docs2': form_data,
            'today_date': now_user_tz.strftime("%d-%m-%Y %H:%M:%S"),
        }
