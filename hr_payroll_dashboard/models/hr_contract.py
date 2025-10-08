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


class Contract(models.Model):
    """
    This class extends the HR Contract model to include additional fields
    and functionalities.
    """
    _inherit = 'hr.contract'

    state_label = fields.Char(compute="_compute_state_label", store=True,
                              help="A representation of the contract state.")

    @api.depends('state')
    def _compute_state_label(self):
        """Compute to get the label value of the contract state"""
        for record in self:
            record.state_label = dict(self._fields['state'].selection).get(
                record.state)

    @api.model
    def get_employee_contract(self):
        """Return employees contract details"""
        cr = self._cr
        cr.execute("""SELECT hr_contract.state_label,count(*) 
        FROM hr_contract 
        JOIN hr_employee ON hr_employee.id=hr_contract.employee_id 
        GROUP BY hr_contract.state_label""")
        dat = cr.fetchall()
        data = [{'label': d[0], 'value': d[1]} for d in dat]
        return data
