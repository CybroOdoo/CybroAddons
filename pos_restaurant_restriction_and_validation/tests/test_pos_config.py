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
from odoo.tests.common import new_test_user
from odoo.addons.point_of_sale.tests.common import TestPoSCommon


@tagged('post_install', '-at_install')
class TestPosConfigRestriction(TestPoSCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.basic_config
        cls.config.write({
            'pos_restaurant_restriction': True,
            'pos_orderline_quantity_update': True,
            'pos_orderline_delete': True,
            'pos_order_delete': True,
            'pos_session_close': True,
        })
        cls.manager = new_test_user(
            cls.env,
            login='pos_restriction_manager',
            groups='base.group_user,point_of_sale.group_pos_manager',
            name='POS Restriction Manager',
            pos_security_pin='2468',
        )
        cls.product = cls.env['product.product'].create({
            'name': 'Restriction Test Product',
            'available_in_pos': True,
            'list_price': 12.0,
        })

    def test_load_pos_data_read_includes_restriction_fields(self):
        # Use the correct Odoo 18 API: _load_pos_data_fields returns the list of
        # fields that will be sent to the POS frontend (same used in _load_pos_data).
        fields = self.env['pos.config']._load_pos_data_fields(self.config.id)
        loaded_config = self.env['pos.config'].search_read(
            [('id', '=', self.config.id)], fields, load=False
        )[0]

        self.assertTrue(loaded_config['pos_restaurant_restriction'])
        self.assertTrue(loaded_config['pos_orderline_quantity_update'])
        self.assertTrue(loaded_config['pos_orderline_delete'])
        self.assertTrue(loaded_config['pos_order_delete'])
        self.assertTrue(loaded_config['pos_session_close'])

    def test_get_managers_for_approval_returns_pos_managers(self):
        managers = self.env['pos.config'].get_managers_for_approval(self.config.id)
        manager_ids = {manager['id'] for manager in managers}

        self.assertIn(self.manager.id, manager_ids)
        self.assertTrue(all({'id', 'name'} <= set(manager) for manager in managers))

    def test_validate_manager_pin_for_restriction_approves_and_logs_action(self):
        before_logs = self.env['pos.action.log'].search([])

        result = self.env['pos.config'].validate_manager_pin_for_restriction(
            self.config.id,
            self.manager.id,
            '2468',
            'orderline_quantity_update',
            product_id=self.product.id,
            old_qty=1.0,
            new_qty=3.0,
            order_ref='ORDER-001',
        )

        new_log = self.env['pos.action.log'].search([]) - before_logs
        self.assertEqual(result, {'approved': True})
        self.assertEqual(len(new_log), 1)
        self.assertEqual(new_log.user_id, self.env.user)
        self.assertEqual(new_log.approved_by, self.manager)
        self.assertEqual(new_log.action_type, 'orderline_quantity_update')
        self.assertEqual(new_log.order_ref, 'ORDER-001')
        self.assertEqual(new_log.product_id, self.product)
        self.assertEqual(new_log.old_qty, 1.0)
        self.assertEqual(new_log.new_qty, 3.0)

    def test_validate_manager_pin_for_restriction_rejects_wrong_pin(self):
        before_logs = self.env['pos.action.log'].search_count([])

        result = self.env['pos.config'].validate_manager_pin_for_restriction(
            self.config.id,
            self.manager.id,
            '0000',
            'delete_order',
            order_ref='ORDER-002',
        )

        self.assertEqual(result, {'approved': False})
        self.assertEqual(self.env['pos.action.log'].search_count([]), before_logs)
