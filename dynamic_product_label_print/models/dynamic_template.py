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


class DynamicTemplate(models.Model):
    """Dynamic template for Products"""
    _name = "dynamic.template"
    _description = 'Dynamic Template'

    name = fields.Char(string='Name', required=True,
                       help='Name of the template')
    bc_height = fields.Char(string='Barcode Height', required=True,
                            help='Height of the barcode')
    bc_width = fields.Char(string='Barcode width', required=True,
                           help='Width of the barcode')
    dynamic_field_ids = fields.One2many('dynamic.fields', 'field_id',
                                        string='Fields',
                                        help='You can select the required field '
                                             'from the product with required '
                                             'size and color for viewing in the '
                                             'label report')
