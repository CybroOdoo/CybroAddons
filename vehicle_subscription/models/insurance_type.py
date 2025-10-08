# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Rahna Rasheed (<https://www.cybrosys.com>)
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
#############################################################################
from odoo import fields, models


class InsuranceType(models.Model):
    """New model insurance type to add fields"""
    _name = "insurance.type"
    _description = "Insurance type"
    _inherit = "mail.thread"

    name = fields.Char(string="Insurance Name",
                       help="This field is used to set name for insurance")
    coverage_ids = fields.One2many('insurance.coverage', 'coverage_id',
                                   string="Coverage",
                                   help="Helps you to give details of coverage")


class InsuranceCoverageType(models.Model):
    """One2many field for insurance type"""
    _name = 'insurance.coverage'
    _description = "Insurance Coverage"

    description = fields.Char(string="Description", help="Detail of coverage")
    coverage_price = fields.Float(string="Price", help="Rate of insurance")
    coverage_id = fields.Many2one('insurance.type',
                                  help="Can choose insurance type")
