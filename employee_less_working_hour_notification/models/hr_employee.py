################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Unnimaya C O (odoo@cybrosys.com)
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
from datetime import timedelta
from odoo import fields, models


class ResConfigSettings(models.Model):
    """"Inherited model containing methods for generating list of less worked
    employees"""
    _inherit = 'hr.employee'

    def action_generate_list(self):
        """Method for generating list of less worked employees"""
        minimum_working_hour = self.env['ir.config_parameter'].sudo().get_param(
            'employee_less_working_hour_notification.minimum_working_hour')
        attendance = self.env['hr.attendance'].search(
            [('worked_hours', '<', minimum_working_hour)]).filtered(
            lambda r: str(r.check_in)[:-9] == str(
                fields.date.today() - timedelta(1)))
        if attendance:
            less_worked_employee_list = []
            non_checkout_employee_list = []
            for rec in attendance:
                employee_detail = {
                    'name': rec.employee_id.name,
                    'department': rec.employee_id.department_id.name,
                    'worked_hours': round(rec.worked_hours, 2),
                }
                if rec.worked_hours == 0:
                    non_checkout_employee_list.append(employee_detail)
                else:
                    less_worked_employee_list.append(employee_detail)
            company_detail = {
                'company': self.env.company.name,
                'email': self.env.company.email,
                'phone': self.env.company.phone,
                'date': fields.date.today() - timedelta(1),
                'minimum_working_hour': minimum_working_hour
            }
            mail_template = self.env.ref(
                'employee_less_working_hour_notification.'
                'mail_template_less_worked_employees').with_context(
                less_worked_employee_list=less_worked_employee_list,
                non_checkout_employee_list=non_checkout_employee_list,
                company_detail=company_detail
            )
            email_values = {
                'email_from': self.env.company.email,
                'email_to': self.env['ir.config_parameter'].sudo().get_param(
                    'employee_less_working_hour_notification.hr_email'),
            }
            mail_template.send_mail(self.id, force_send=True,
                                    email_values=email_values)
