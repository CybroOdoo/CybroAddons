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
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestStockLocation(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.source_location = cls.env['stock.location'].create({
            'name': 'Configured POS Location',
            'usage': 'internal',
        })
        cls.other_location = cls.env['stock.location'].create({
            'name': 'Other POS Location',
            'usage': 'internal',
        })
        cls.source_product = cls.env['product.product'].create({
            'name': 'Product In Configured Location',
            'is_storable': True,
            'available_in_pos': True,
        })
        cls.other_product = cls.env['product.product'].create({
            'name': 'Product In Other Location',
            'is_storable': True,
            'available_in_pos': True,
        })
        cls._update_quantity(cls.source_product, cls.source_location, 5)
        cls._update_quantity(cls.other_product, cls.other_location, 5)

    @classmethod
    def _update_quantity(cls, product, location, quantity):
        cls.env['stock.quant'].with_context(inventory_mode=True).create({
            'product_id': product.id,
            'location_id': location.id,
            'inventory_quantity': quantity,
        }).action_apply_inventory()

    def test_search_products_by_location_returns_configured_location_products(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'pos_load_products_location.source_loc_id',
            self.source_location.id,
        )

        product_tmpl_ids = self.env['stock.location'].search_products_by_location()

        self.assertIn(self.source_product.product_tmpl_id.id, product_tmpl_ids)
        self.assertNotIn(self.other_product.product_tmpl_id.id, product_tmpl_ids)
