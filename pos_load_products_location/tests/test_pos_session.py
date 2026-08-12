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
from unittest.mock import patch

from odoo.addons.point_of_sale.tests.common import TestPoSCommon
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestPoSSession(TestPoSCommon):

    def setUp(self):
        super().setUp()
        self.config = self.basic_config
        self.session = self.open_new_session()
        self.source_location = self.config.picking_type_id.default_location_src_id
        self.stocked_product = self.create_product(
            'Stocked POS Product',
            self.categ_basic,
            10.0,
        )
        self.unstocked_product = self.create_product(
            'Unstocked POS Product',
            self.categ_basic,
            20.0,
        )
        self._update_quantity(self.stocked_product, self.source_location, 4)

    def _update_quantity(self, product, location, quantity):
        self.env['stock.quant'].with_context(inventory_mode=True).create({
            'product_id': product.id,
            'location_id': location.id,
            'inventory_quantity': quantity,
        }).action_apply_inventory()

    def _product_params(self):
        return {
            'context': {},
            'search_params': {
                'domain': [('id', 'in', [self.stocked_product.id, self.unstocked_product.id])],
                'fields': ['id', 'name'],
                'order': 'id',
            },
        }

    def _disable_product_processing(self):
        patcher = patch.object(
            type(self.session),
            '_process_pos_ui_product_product',
            lambda session, products: None,
            create=True,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_get_pos_ui_product_product_filters_search_read_by_source_stock(self):
        self._disable_product_processing()
        self.config.limited_products_loading = False

        products = self.session._get_pos_ui_product_product(self._product_params())

        self.assertEqual([product['id'] for product in products], [self.stocked_product.id])

    def test_get_pos_ui_product_product_filters_limited_products_by_source_stock(self):
        self._disable_product_processing()
        self.config.limited_products_loading = True
        limited_products = [
            {'id': self.stocked_product.id, 'name': self.stocked_product.name},
            {'id': self.unstocked_product.id, 'name': self.unstocked_product.name},
        ]

        def _get_limited_products_loading(config, fields):
            self.assertEqual(fields, ['id', 'name'])
            return limited_products

        with patch.object(
            type(self.config),
            'get_limited_products_loading',
            _get_limited_products_loading,
            create=True,
        ):
            products = self.session._get_pos_ui_product_product(self._product_params())

        self.assertEqual([product['id'] for product in products], [self.stocked_product.id])
