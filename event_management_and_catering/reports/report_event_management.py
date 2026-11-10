# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
################################################################################
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ReportHotelManagement(models.AbstractModel):
    """Class for fetch and carry off pdf data to template"""
    _name = "report.event_management_and_catering.report_event_management"
    _description = "Event Management Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        """Get values for the Event Management report"""

        form_data = data.get('form', {})

        # ---------------------------
        # Validations
        # ---------------------------
        if form_data.get('date_from') and form_data.get('date_to') and \
                form_data['date_from'] > form_data['date_to']:
            raise ValidationError(self.env._('From Date must be less than To Date'))

        # ---------------------------
        # Dynamic domain conditions
        # ---------------------------
        domain = []
        if form_data.get('partner_id'):
            domain.append(('partner_id', '=', form_data['partner_id'][0]))
        if form_data.get('date_from'):
            domain.append(('date', '>=', form_data['date_from']))
        if form_data.get('date_to'):
            domain.append(('date', '<=', form_data['date_to']))
        if form_data.get('type_event_ids'):
            event_list = data.get('event_types', [])
            if event_list:
                domain.append(('type_of_event_id', 'in', event_list))
        if form_data.get('event_state'):
            domain.append(('state', '=', form_data['event_state']))

        events = self.env['event.management'].search(domain, order='date')
        rec = [{
            'event': ev.name or '',
            'type': ev.type_of_event_id.name or '',
            'partner': ev.partner_id.name or '',
            'state': ev.state or '',
            'date': ev.date,
            'start_date': ev.start_date,
            'end_date': ev.end_date,
        } for ev in events]

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
