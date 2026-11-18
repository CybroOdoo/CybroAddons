# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import fields, models


class ProductTemplate(models.Model):
    """Extend product templates with package category configuration."""

    _inherit = 'product.template'

    package_category_id = fields.Many2one(
        'package.category',
        help="Category used to group products into separate packages",
    )
    package_split_value = fields.Boolean(
        compute='_compute_package_split_value',
        help="Set to true when the package split setting is enabled",
    )

    def _compute_package_split_value(self):
        """Compute package split visibility from system configuration parameters."""
        value = self.env['ir.config_parameter'].sudo().get_bool(
            'package_split.enable_package_split',
        )
        for record in self:
            record.package_split_value = value
