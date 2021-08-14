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


class HrEmployeeVaccineCentre(models.Model):
    _name = 'hr.employee.vaccine.centre'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Vaccine Centre'
    _rec_name = 'name'

    name = fields.Char(string=_("Centre Name"), required=1)
    contact_details = fields.Char(string=_("Contact Details"))
    other_info = fields.Text(string=_("Other Details"))


