# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import ast
import os

from odoo.modules.module import get_manifest, get_module_path
from odoo.tests import TransactionCase, tagged
from odoo.tools.translate import xml_translate

from odoo.addons.point_of_sale.tests.common import CommonPosTest

_MODULE = 'total_quantity_pos'


@tagged('post_install', '-at_install')
class TestTotalQuantityPos(TransactionCase):

    def test_pos_config_fields_exist(self):
        pos_config_fields = self.env['pos.config']._fields
        self.assertIn('pos_total_items', pos_config_fields)
        self.assertIn('pos_total_quantity', pos_config_fields)
        self.assertEqual(pos_config_fields['pos_total_items'].type, 'boolean')
        self.assertEqual(pos_config_fields['pos_total_quantity'].type, 'boolean')

    def test_pos_config_fields_default_to_false(self):
        config = self.env['pos.config'].create({'name': 'Default Flags Shop'})
        self.assertFalse(config.pos_total_items)
        self.assertFalse(config.pos_total_quantity)

    def test_settings_fields_exist(self):
        settings_fields = self.env['res.config.settings']._fields
        self.assertIn('total_items', settings_fields)
        self.assertIn('total_quantity', settings_fields)
        self.assertEqual(settings_fields['total_items'].related, 'pos_config_id.pos_total_items')
        self.assertEqual(settings_fields['total_quantity'].related, 'pos_config_id.pos_total_quantity')
        self.assertFalse(settings_fields['total_items'].readonly)
        self.assertFalse(settings_fields['total_quantity'].readonly)

    def test_settings_fields_default_to_false(self):
        config = self.env['pos.config'].create({'name': 'Related Flags Shop'})
        settings = self.env['res.config.settings'].create({'pos_config_id': config.id})
        self.assertFalse(settings.total_items)
        self.assertFalse(settings.total_quantity)

    def test_settings_fields_related_to_pos_config(self):
        """ The settings read the flag stored on the selected PoS config. """
        config = self.env['pos.config'].create({'name': 'Read Through Shop'})
        config.write({'pos_total_items': True, 'pos_total_quantity': False})
        config.invalidate_recordset()
        settings = self.env['res.config.settings'].create({'pos_config_id': config.id})
        self.assertTrue(settings.total_items)
        self.assertFalse(settings.total_quantity)

    def test_settings_write_propagates_to_pos_config(self):
        """ Toggling a settings field updates the field on the PoS config. """
        config = self.env['pos.config'].create({'name': 'Write Through Shop'})
        settings = self.env['res.config.settings'].create({'pos_config_id': config.id})
        settings.write({'total_items': True, 'total_quantity': True})
        config.invalidate_recordset()
        self.assertTrue(config.pos_total_items)
        self.assertTrue(config.pos_total_quantity)

    def test_settings_view_contains_settings(self):
        view = self.env.ref(
            'total_quantity_pos.res_config_settings_view_form',
            raise_if_not_found=False)
        self.assertTrue(view)
        arch = view.arch
        self.assertIn('total_items_setting', arch)
        self.assertIn('total_quantity_setting', arch)
        self.assertIn('total_items', arch)
        self.assertIn('total_quantity', arch)

    def test_settings_view_uses_setting_elements(self):
        """ Both flags are rendered as <setting> inside their settings block. """
        view = self.env.ref('total_quantity_pos.res_config_settings_view_form')
        arch = view.arch
        self.assertIn('<setting', arch)
        self.assertEqual(arch.count('total_items_setting'), 1)
        self.assertEqual(arch.count('total_quantity_setting'), 1)
        self.assertIn('pos_interface_section', arch)
        self.assertIn('pos_bills_and_receipts_section', arch)
        self.assertNotIn('o_setting_box', arch)

    def test_receipt_template_respects_setting(self):
        view = self.env.ref(
            'total_quantity_pos.pos_order_receipt_total_quantity',
            raise_if_not_found=False)
        self.assertTrue(view)
        self.assertIn('pos_total_quantity', view.arch)

    def test_receipt_template_gated_and_labeled(self):
        """ The totals block is hidden by the setting and labelled as required. """
        view = self.env.ref('total_quantity_pos.pos_order_receipt_total_quantity')
        arch = view.arch
        self.assertIn("config.get('pos_total_quantity')", arch)
        self.assertIn("extra_data['total_item_count']", arch)
        self.assertIn('Total Items', arch)
        self.assertIn('Total Quantity', arch)
        self.assertIn('name="total_item_count"', arch)

    def test_order_display_asset_references_setting_and_getters(self):
        """ The OWL template shows both totals only when the flag is set. """
        widget_xml = os.path.join(
            get_module_path(_MODULE),
            'static/src/overrides/components/order_widget.xml')
        with open(widget_xml, encoding='utf-8') as f:
            arch = f.read()
        self.assertIn('pos_total_items', arch)
        self.assertIn('itemCount', arch)
        self.assertIn('totalQuantity', arch)
        self.assertIn('t-inherit="point_of_sale.OrderDisplay"', arch)

    def test_order_widget_js_getters(self):
        """ The patched getters return the line count and the quantity sum. """
        widget_js = os.path.join(
            get_module_path(_MODULE),
            'static/src/overrides/components/order_widget.js')
        with open(widget_js, encoding='utf-8') as f:
            source = f.read()
        for getter in ('get itemCount', 'get totalQuantity', 'getOrderlines',
                       'patch(OrderDisplay.prototype'):
            self.assertIn(getter, source)

    def test_manifest_declares_views_and_assets(self):
        manifest = get_manifest(_MODULE)
        self.assertIn('views/res_config_settings_views.xml', manifest['data'])
        self.assertIn('views/pos_order_receipt_templates.xml', manifest['data'])
        asset_bundle = manifest['assets']['point_of_sale._assets_pos']
        self.assertIn(
            'total_quantity_pos/static/src/overrides/components/order_widget.js',
            asset_bundle)
        self.assertIn(
            'total_quantity_pos/static/src/overrides/components/order_widget.xml',
            asset_bundle)

    def test_manifest_is_lgpl(self):
        manifest = get_manifest(_MODULE)
        self.assertEqual(manifest['license'], 'LGPL-3')
        self.assertNotIn('pos_self_order', manifest['depends'])

    def test_xml_templates_are_well_formed(self):
        module_path = get_module_path(_MODULE)
        xml_paths = [
            os.path.join(module_path, 'views/res_config_settings_views.xml'),
            os.path.join(module_path,
                         'views/pos_order_receipt_templates.xml'),
            os.path.join(module_path,
                         'static/src/overrides/components/order_widget.xml'),
        ]
        with open(os.path.join(module_path, 'tests/test_total_quantity_pos.py'),
                  encoding='utf-8') as f:
            ast.parse(f.read())
        for path in xml_paths:
            with open(path, 'rb') as f:
                xml_translate(lambda term: term, f.read())


@tagged('post_install', '-at_install')
class TestTotalQuantityPosScenarios(CommonPosTest):
    """ Functional scenarios for an order on the POS screen and its receipt. """

    _test_user_groups = None  # FIXME list needed groups

    def _create_totals_order(self):
        order, _refund = self.create_backend_pos_order({
            'pos_config': self.pos_config_usd,
            'line_data': [
                {'product_id': self.ten_dollars_no_tax.product_variant_id.id,
                 'qty': 3,
                 'price_subtotal': 0.0,
                 'price_subtotal_incl': 0.0},
                {'product_id': self.twenty_dollars_no_tax.product_variant_id.id,
                 'qty': 2,
                 'price_subtotal': 0.0,
                 'price_subtotal_incl': 0.0},
            ],
        })
        return order

    def test_order_item_count_and_total_quantity(self):
        order = self._create_totals_order()
        self.assertEqual(len(order.lines), 2)
        self.assertEqual(sum(order.lines.mapped('qty')), 5)

    def test_receipt_data_total_item_count(self):
        """ Receipt extra data agrees with the quantity sum of the lines. """
        order = self._create_totals_order()
        extra = order.order_receipt_generate_data()['extra_data']
        self.assertEqual(extra['total_item_count'], 5)
        self.assertNotEqual(extra['total_item_count'], len(order.lines))

    def test_receipt_config_includes_module_setting(self):
        """ The flag reaches the receipt through the config values. """
        order = self._create_totals_order()
        data = order.order_receipt_generate_data()
        self.assertIn('pos_total_quantity', data['config'])
        self.assertFalse(data['config']['pos_total_quantity'])

    def test_receipt_shows_totals_when_enabled(self):
        order = self._create_totals_order()
        self.pos_config_usd.write({'pos_total_quantity': True})
        data = order.order_receipt_generate_data()
        self.assertTrue(data['config']['pos_total_quantity'])
        html = self.env['ir.qweb']._render(
            'point_of_sale.pos_order_receipt', values=data)
        self.assertIn('Total Items', html)
        self.assertIn('Total Quantity', html)

    def test_receipt_hides_totals_when_disabled(self):
        order = self._create_totals_order()
        self.pos_config_usd.write({'pos_total_quantity': False})
        data = order.order_receipt_generate_data()
        html = self.env['ir.qweb']._render(
            'point_of_sale.pos_order_receipt', values=data)
        self.assertNotIn('Total Items', html)
        self.assertNotIn('Total Quantity', html)
