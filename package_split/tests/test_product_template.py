# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
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

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestProductTemplate(TransactionCase):
    def test_compute_package_split_value_reads_config_parameter(self):
        product = self.env['product.template'].create({
            'name': 'Package Split Product',
        })
        self.env['ir.config_parameter'].sudo().set_param(
            'package_split.enable_package_split', True)

        product._compute_package_split_value()

        self.assertTrue(product.package_split_value)

    def test_package_category_can_be_set_on_product_template(self):
        category = self.env['package.category'].create({'name': 'Frozen'})
        product = self.env['product.template'].create({
            'name': 'Categorized Product',
            'package_category_id': category.id,
        })

        self.assertEqual(product.package_category_id, category)
