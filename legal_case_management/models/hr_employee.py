# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: MOHAMMED DILSHAD TK (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class HrEmployee(models.Model):
    """To create lawyers"""
    _inherit = 'hr.employee'

    is_lawyer = fields.Boolean("Is Lawyer", help='Is this employee is a lawyer')
    wage_per_trial = fields.Integer("Wage Per Trial", help='Wage per trial')
    wage_per_case = fields.Integer("Wage Per Case", help='Wage per Case')
    not_available = fields.Boolean('Not Available', default=False,
                                   help='Lawyer Unavailable')
