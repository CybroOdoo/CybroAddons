# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################

from odoo import models, fields, api, _


class HrEmployeeInherit(models.AbstractModel):
    _inherit = 'hr.employee.base'

    employee_vaccination_ids = fields.One2many('vaccination.detail', 'employee_id', string=_("Vaccination Information"))
    vaccine_dose_count = fields.Integer(string=_("Dose"), compute='_compute_vaccination_status')
    vaccine_note = fields.Text(string='Other Details')
    vaccination_status = fields.Selection(
        selection=[('no', 'Not Vaccinated'), ('full', 'Fully Vaccinated')],
        compute='_compute_vaccination_status', string="Vaccination Status")

    @api.depends('employee_vaccination_ids.vaccine_id')
    def _compute_vaccination_status(self):
        for employee in self:
            if len(employee.employee_vaccination_ids) == 0:
                employee.vaccination_status = 'no'
            else:
                employee.vaccination_status = 'full'
            employee.vaccine_dose_count = len(employee.employee_vaccination_ids)
