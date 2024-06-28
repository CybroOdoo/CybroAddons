# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import fields, models


class DentalTreatment(models.Model):
    """For adding Dental treatment details of the patients"""
    _name = 'dental.treatment'
    _description = "Dental Treatment"
    _inherit = ['mail.thread']

    name = fields.Char(string='Treatment Name', help="Date of the treatment")
    treatment_categ_id = fields.Many2one('treatment.category',
                                         string="Category",
                                         help="name of the treatment")
    cost = fields.Float(string='Cost',
                        help="Cost of the Treatment")
