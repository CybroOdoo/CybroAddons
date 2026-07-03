# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
import odoo

from odoo.addons.point_of_sale.tests.common import TestPoSCommon


@odoo.tests.tagged('post_install', '-at_install')
class TestPosMultiVariant(TestPoSCommon):
    """Validate the custom POS variant fields and session loaders."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.attribute = cls.env['product.attribute'].create({
            'name': 'Size',
        })
        cls.value_small = cls.env['product.attribute.value'].create({
            'name': 'Small',
            'attribute_id': cls.attribute.id,
        })
        cls.value_large = cls.env['product.attribute.value'].create({
            'name': 'Large',
            'attribute_id': cls.attribute.id,
        })
        cls.product_template = cls.env['product.template'].create({
            'name': 'Variant Test Product',
            'available_in_pos': True,
            'list_price': 25.0,
            'is_pos_variants': True,
        })
        cls.variant_line = cls.env['variants.tree'].create({
            'variants_id': cls.product_template.id,
            'attribute_id': cls.attribute.id,
            'value_ids': [(6, 0, [cls.value_small.id, cls.value_large.id])],
            'extra_price': 4.5,
        })
        cls.session = cls.env['pos.session'].create({
            'name': 'POS Multi Variant Test Session',
            'config_id': cls.basic_config.id,
            'user_id': cls.env.user.id,
            'state': 'opened',
        })

    def test_product_template_fields(self):
        self.assertTrue(self.product_template.is_pos_variants)
        self.assertEqual(self.product_template.variant_line_ids, self.variant_line)
        self.assertEqual(self.variant_line.variants_id, self.product_template)

    def test_variants_tree_fields(self):
        self.assertEqual(self.variant_line.attribute_id, self.attribute)
        self.assertEqual(
            self.variant_line.value_ids,
            self.value_small | self.value_large,
        )
        self.assertEqual(self.variant_line.extra_price, 4.5)

    def test_pos_ui_models_to_load(self):
        models_to_load = self.session._pos_ui_models_to_load()

        self.assertIn('variants.tree', models_to_load)
        self.assertIn('product.attribute.value', models_to_load)
        self.assertEqual(models_to_load.count('variants.tree'), 1)
        self.assertEqual(models_to_load.count('product.attribute.value'), 1)

    def test_loader_params_variants_tree(self):
        params = self.session._loader_params_variants_tree()

        self.assertEqual(
            params,
            {
                'search_params': {
                    'fields': ['value_ids', 'attribute_id', 'variants_id', 'extra_price'],
                },
            },
        )

    def test_loader_params_product_attribute_value(self):
        params = self.session._loader_params_product_attribute_value()

        self.assertEqual(
            params,
            {
                'search_params': {
                    'fields': ['id', 'name'],
                },
            },
        )

    def test_get_pos_ui_variants_tree(self):
        params = self.session._loader_params_variants_tree()
        params['search_params']['domain'] = [('id', '=', self.variant_line.id)]
        records = self.session._get_pos_ui_variants_tree(params)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['attribute_id'][0], self.attribute.id)
        self.assertEqual(records[0]['variants_id'][0], self.product_template.id)
        self.assertEqual(set(records[0]['value_ids']), set(self.variant_line.value_ids.ids))
        self.assertEqual(records[0]['extra_price'], self.variant_line.extra_price)

    def test_get_pos_ui_product_attribute_value(self):
        params = self.session._loader_params_product_attribute_value()
        params['search_params']['domain'] = [('id', 'in', (self.value_small | self.value_large).ids)]
        records = self.session._get_pos_ui_product_attribute_value(params)

        self.assertEqual(len(records), 2)
        self.assertEqual(
            {record['id'] for record in records},
            set((self.value_small | self.value_large).ids),
        )
        self.assertEqual(
            {record['name'] for record in records},
            {'Small', 'Large'},
        )

    def test_loader_params_product_product(self):
        params = self.session._loader_params_product_product()
        fields = params['search_params']['fields']

        self.assertIn('is_pos_variants', fields)
        self.assertIn('variant_line_ids', fields)
        self.assertEqual(fields.count('is_pos_variants'), 1)
        self.assertEqual(fields.count('variant_line_ids'), 1)
