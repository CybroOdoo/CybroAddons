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
from odoo import api, fields, models


class HrLeave(models.Model):
    """
    This class extends the HR Leave model to include additional fields
    and functionalities specific to the requirements of the application.
    """
    _inherit = 'hr.leave'

    state_string = fields.Char(compute="_compute_state_string", store=True,
                               help="A representation of the leave state.")

    @api.depends('state')
    def _compute_state_string(self):
        """Compute the label of the leave state"""
        for rec in self:
            rec.state_string = dict(self._fields[
                                        'state'].selection).get(rec.state)

    @api.model
    def get_employee_time_off(self):
        """Return employee time off details"""
        self._cr.execute("""SELECT hr_leave.state_string, count(*) 
        FROM hr_employee JOIN hr_leave ON hr_leave.employee_id=hr_employee.id 
        GROUP BY hr_leave.state_string""")
        dat = self._cr.fetchall()
        data = [{'label': d[0], 'value': d[1]} for d in dat]
        return data
