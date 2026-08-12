# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
