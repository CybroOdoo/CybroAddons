# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import fields, models


class DisciplineCategory(models.Model):
    """Model for discipline categories"""
    _name = 'discipline.category'
    _description = 'Discipline Category'

    code = fields.Char(string="Code", required=True,
                       help="Discipline category code")
    name = fields.Char(string="Name", required=True,
                       help=" Discipline category name")
    category_type = fields.Selection([('disciplinary', 'Disciplinary Category'),
                                      ('action', 'Action Category')],
                                     string="Category Type",
                                     help="Choose the category type "
                                          "disciplinary or action")
    description = fields.Text(string="Details",
                              help="Details for this category")
