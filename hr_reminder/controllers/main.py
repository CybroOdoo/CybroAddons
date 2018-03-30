# -*- coding: utf-8 -*-
###################################################################################
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Treesa Maria Jude  (<https://www.cybrosys.com>)
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

from odoo import http
from odoo.http import request


class Reminders(http.Controller):

    @http.route('/hr_reminder/all_reminder', type='json', auth="public")
    def all_reminder(self):
        reminder = []
        for i in request.env['hr.reminder'].search([]):
            if i.reminder_active:
                reminder.append(i.name)
        return reminder

    @http.route('/hr_reminder/reminder_active', type='json', auth="public")
    def reminder_active(self, **kwargs):
        reminder_value = kwargs.get('reminder_name')
        value = []

        for i in request.env['hr.reminder'].search([('name', '=', reminder_value)]):
            value.append(i.model_name.model)
            value.append(i.model_field.name)
            value.append(i.search_by)
            value.append(i.date_set)
            value.append(i.date_from)
            value.append(i.date_to)
            # value.append(i.exclude_year)
        return value
