# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Avinash Nk(<avinash@cybrosys.in>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from odoo import models, api


class EventReportParser(models.AbstractModel):
    _name = 'report.event_management_report.event_report_template'

    @api.model
    def render_html(self, docids, data):
        filtered_events = self.filtered_records(data)
        docargs = {
            'docs': filtered_events,
            'model': self,
            'data': data,
        }
        return self.env['report'].render('event_management_report.event_report_template', docargs)

    @api.multi
    def filtered_records(self, data):
        total_events = self.env['event.management']
        type_select = data['type_select']
        state_select = data['state_select']
        domain = [('type_of_event', 'in', type_select)]
        if state_select:
            domain.append(('state', '=', state_select))
        filtered_events = total_events.search(domain)
        return filtered_events
