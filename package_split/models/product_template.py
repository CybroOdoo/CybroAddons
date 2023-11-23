# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Muhsina V (<https://www.cybrosys.com>)
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


class ProductTemplate(models.Model):
    """Inhering to add new field for package category"""
    _inherit = 'product.template'

    package_category_id = fields.Many2one(
        'package.category', string="Package Category", help="Package category")
    package_split_value = fields.Boolean(
        string='Package Split Value', compute='_compute_package_split_value',
        help="This field value is set to true if the field to enable package "
             "split is enabled")

    def _compute_package_split_value(self):
        """function to set value to the field package_split_value from
         system parameter"""
        self.package_split_value = self.env['ir.config_parameter'].sudo(
        ).get_param(
            'package_split.enable_package_split')
