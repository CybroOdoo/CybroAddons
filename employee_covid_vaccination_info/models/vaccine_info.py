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


class HrEmployeeVaccineInfo(models.Model):
    _name = 'hr.employee.vaccine.info'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Vaccine Details'
    _rec_name = 'name'

    name = fields.Char(string=_("Vaccine Name"), required=1)
    dose = fields.Integer(string=_("No.of Doses"), default=1, help="Number of doses required")
    period = fields.Integer(string=_("Interval Between Doses"), default=30, help="Period between two doses in days")
    company = fields.Char(string=_("Company"))
    country_id = fields.Many2one('res.country', string='Country of Origin')
    vaccine_details = fields.Html(string=_("Vaccine Details"))


