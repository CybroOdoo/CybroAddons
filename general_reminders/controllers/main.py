# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Cybrosys Technologies(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.addons.web import http
from openerp.addons.web.http import request


class Reminders(http.Controller):

    @http.route('/general_reminders/all_reminder', type='json', auth="public")
    def all_reminder(self):
        reminder = []
        for i in request.env['popup.reminder'].search([]):
            reminder.append(i.name)
        return reminder

    @http.route('/general_reminders/reminder_active', type='json', auth="public")
    def reminder_active(self, **kwargs):
        reminder_value = kwargs.get('reminder_name')
        value = []

        for i in request.env['popup.reminder'].search([('name', '=', reminder_value)]):
            value.append(i.model_name.model)
            value.append(i.model_field.name)
            value.append(i.search_by)
            value.append(i.date_set)
            value.append(i.date_from)
            value.append(i.date_to)
        return value
