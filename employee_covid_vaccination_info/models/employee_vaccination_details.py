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

from odoo import models, fields, _, api


class HrEmployeeVaccinationDetails(models.Model):
    _name = 'vaccination.detail'
    _description = "Vaccination Details"

    employee_id = fields.Many2one('hr.employee', string="Employee")
    sequence = fields.Integer(string='Sequence', default=10)

    vaccine_id = fields.Many2one('hr.employee.vaccine.info', string=_("Vaccine"), ondelete='restrict')
    vaccination_centre_id = fields.Many2one('hr.employee.vaccine.centre', string=_("Vaccination Centre"),
                                            ondelete='restrict')
    vaccinated_by = fields.Char(string=_("Vaccinated By"))
    vaccine_dose = fields.Char(string=_("Dose"))
    dose_date = fields.Date(string=_("Vaccinated Date"))

    vaccinated_country_id = fields.Many2one('res.country', string='Vaccinated Country')
    vaccinated_state_id = fields.Many2one('res.country.state', string='Vaccinated State',
                                          domain="[('country_id', '=?', vaccinated_country_id)]")
    vaccine_company = fields.Char(string=_("Vaccine Company"))

    vaccine_certificate_ids = fields.Many2many(
        'ir.attachment', 'hr_employee_vaccine_certificate_rel', string='Certificates')

    @api.onchange('vaccine_id')
    def onchange_vaccine_id(self):
        if self.vaccine_id:
            self.vaccine_company = self.vaccine_id.company
