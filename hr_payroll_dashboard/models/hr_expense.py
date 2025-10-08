# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
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
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.http import request


class HrExpense(models.Model):
    """
    This class extends the HR Expense model to include additional fields
    and functionalities.
    """
    _inherit = 'hr.expense'

    state_label = fields.Char(compute="_compute_state_label", store=True)

    @api.depends('state')
    def _compute_state_label(self):
        """Compute function for the expense state label"""
        for record in self:
            record.state_label = dict(self._fields['state'].selection).get(
                record.state)

    @api.model
    def get_employee_expense(self):
        """Return employee expense details"""
        cr = self._cr
        month_list = [format(datetime.now() - relativedelta(months=i), '%B %Y')
                      for i in range(11, -1, -1)]
        approved_trend = [{'l_month': month, 'count': 0}
                          for month in month_list]
        uid = request.session.uid
        employee = False
        employee_user = self.env['hr.employee'].sudo().search_read([
            ('user_id', '=', uid)
        ], limit=1)
        employees = self.env['hr.employee'].sudo().search_read([], limit=1)
        if employee_user:
            employee = self.env['hr.employee'].sudo().search_read([
                ('user_id', '=', uid)
            ], limit=1)
        elif employees:
            employee = self.env['hr.employee'].sudo().search_read([], limit=1)
        if employee:
            employee_id = self.env['hr.employee'].browse(employee[0]['id'])
            if not employee_id.is_manager:
                sql = ('''select to_char(date, 'Month YYYY') as l_month, 
                        count(id) from hr_expense
                        WHERE date BETWEEN CURRENT_DATE - INTERVAL '12 months'
                        AND CURRENT_DATE + interval '1 month - 1 day' 
                        AND hr_expense.employee_id = %s
                        group by l_month''')
                self.env.cr.execute(sql, (employee[0]['id'],))
            else:
                sql = ('''select to_char(date, 'Month YYYY') as l_month, 
                count(id) from hr_expense WHERE date 
                BETWEEN CURRENT_DATE - INTERVAL 
                '12 months' AND CURRENT_DATE + interval '1 month - 1 day' 
                group by l_month''')
                self.env.cr.execute(sql)
            approved_data = cr.fetchall()
            for line in approved_data:
                match = list(filter(lambda d: d['l_month'].replace(
                    ' ', '') == line[0].replace(' ', ''), approved_trend))
                if match:
                    match[0]['count'] = line[1]
            for expense in approved_trend:
                expense['l_month'] = expense[
                                         'l_month'].split(' ')[:1][0].strip()[
                                     :3]
            graph_result = [{
                'values': approved_trend
            }]
            return graph_result
        else:
            return False
