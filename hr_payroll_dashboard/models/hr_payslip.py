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
from odoo import api ,fields, models


class HrPayslip(models.Model):
    """    
    This class extends the Hr Payslip model to include additional fields
    and functionalities.
    """
    _inherit = 'hr.payslip'
    _description = 'Employee Payroll'

    payslip_state = fields.Char(compute="_compute_payslip_state", store=True,
                                help="A representation of the payslip state.")

    @api.depends('state')
    def _compute_payslip_state(self):
        """Compute the label value of the payslip state"""
        for rec in self:
            rec.payslip_state = dict(self._fields[
                                            'state'].selection).get(rec.state)

    @api.model
    def get_employee_payslips(self):
        """Return employee payslip details"""
        self._cr.execute(
            """SELECT hr_payslip.payslip_state,count(*) FROM hr_employee 
            JOIN hr_payslip ON hr_payslip.employee_id=hr_employee.id 
            GROUP BY hr_payslip.payslip_state
            """)
        dat = self._cr.fetchall()
        data = [{'label': d[0], 'value': d[1]} for d in dat if d[0] is not None]
        return data
