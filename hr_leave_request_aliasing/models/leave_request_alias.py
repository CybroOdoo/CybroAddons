# -*- coding: utf-8 -*-
###################################################################################
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Jesni Banu (<https://www.cybrosys.com>)
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
import re
from datetime import datetime, timedelta
from odoo import models, api
from odoo.tools import email_split


class HrLeaveAlias(models.Model):
    _inherit = 'hr.holidays'

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """This function extracts required fields of hr.holidays from incoming mail then creating records"""
        try:
            if custom_values is None:
                custom_values = {}
            msg_subject = msg_dict.get('subject', '')
            subject = re.search('LEAVE REQUEST', msg_subject)
            if subject is not None:
                email_address = email_split(msg_dict.get('email_from', False))[0]
                employee = self.env['hr.employee'].sudo().search([
                    '|',
                    ('work_email', 'ilike', email_address),
                    ('user_id.email', 'ilike', email_address)
                ], limit=1)
                msg_body = msg_dict.get('body', '')
                cleaner = re.compile('<.*?>')
                clean_msg_body = re.sub(cleaner, '', msg_body)
                date_list = re.findall(r'\d{2}/\d{2}/\d{4}', clean_msg_body)
                if len(date_list) > 0:
                    date_from = date_list[0]
                    if len(date_list) > 1:
                        start_date = datetime.strptime(date_list[1], '%d/%m/%Y')
                        date_to = start_date + timedelta(days=0)
                    else:
                        start_date = datetime.strptime(date_list[0], '%d/%m/%Y')
                        date_to = start_date + timedelta(days=1)
                    no_of_days_temp = (datetime.strptime(str(date_to), "%Y-%m-%d %H:%M:%S") -
                                       datetime.strptime(date_from, '%d/%m/%Y')).days
                    custom_values.update({
                        'name': msg_subject.strip(),
                        'employee_id': employee.id,
                        'holiday_status_id': 1,
                        'date_from': date_from,
                        'date_to': date_to,
                        'no_of_days_temp': no_of_days_temp
                    })
            return super(HrLeaveAlias, self).message_new(msg_dict, custom_values)
        except:
            pass


