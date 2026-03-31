# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    """Inherit the product category for restricted the users for
     particular products"""
    _inherit = 'product.template'

    restrict_user_ids = fields.Many2many(comodel_name='res.users',
                                         string="Restrict users",
                                         help="Restrict the users for "
                                              "particular products")
    is_product = fields.Boolean(string='Product Restriction',
                                default=True,
                                help="Enable product restriction")
    is_category = fields.Boolean(string='Category Restriction',
                                 default=True,
                                 help="Enable category restriction")
