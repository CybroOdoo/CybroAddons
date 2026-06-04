# -*- coding: utf-8 -*-
from odoo.tests import tagged
from odoo.addons.point_of_sale.tests.common import TestPoSCommon


@tagged('post_install', '-at_install')
class TestResConfigSettingsRestriction(TestPoSCommon):

    def test_settings_fields_write_through_to_pos_config(self):
        config = self.basic_config
        config.write({
            'pos_restaurant_restriction': False,
            'pos_orderline_quantity_update': False,
            'pos_orderline_delete': False,
            'pos_order_delete': False,
            'pos_session_close': False,
        })

        settings = self.env['res.config.settings'].create({'pos_config_id': config.id})
        settings.write({
            'pos_restaurant_restriction': True,
            'pos_orderline_quantity_update': True,
            'pos_orderline_delete': True,
            'pos_order_delete': True,
            'pos_session_close': True,
        })

        self.assertTrue(config.pos_restaurant_restriction)
        self.assertTrue(config.pos_orderline_quantity_update)
        self.assertTrue(config.pos_orderline_delete)
        self.assertTrue(config.pos_order_delete)
        self.assertTrue(config.pos_session_close)

    def test_settings_fields_are_editable_related_fields(self):
        settings_fields = self.env['res.config.settings']._fields

        for field_name in (
            'pos_restaurant_restriction',
            'pos_orderline_quantity_update',
            'pos_orderline_delete',
            'pos_order_delete',
            'pos_session_close',
        ):
            field = settings_fields[field_name]
            self.assertEqual(field.related, f'pos_config_id.{field_name}')
            self.assertFalse(field.readonly)
