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
#############################################################################
from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPosSession(TransactionCase):
    """Test suite for POS session order fetching and configuration methods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.icp = cls.env['ir.config_parameter'].sudo()
        cls.pos_session_model = cls.env['pos.session']

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test POS Customer',
        })

        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test POS Config',
        })

        cls.pos_session = cls.env['pos.session'].create({
            'config_id': cls.pos_config.id,
            'user_id': cls.env.user.id,
        })

        now = fields.Datetime.now()
        ten_days_ago = now - timedelta(days=10)

        # 1. Normal paid order in current session
        cls.order_paid = cls.env['pos.order'].create({
            'session_id': cls.pos_session.id,
            'partner_id': cls.partner.id,
            'amount_total': 120.0,
            'amount_paid': 120.0,
            'amount_tax': 0.0,
            'amount_return': 0.0,
            'state': 'paid',
            'pos_reference': 'POS-REF-001',
            'date_order': now,
        })

        # 2. Draft order without partner in current session
        cls.order_draft = cls.env['pos.order'].create({
            'session_id': cls.pos_session.id,
            'partner_id': False,
            'amount_total': 45.0,
            'amount_paid': 0.0,
            'amount_tax': 0.0,
            'amount_return': 0.0,
            'state': 'draft',
            'pos_reference': 'POS-REF-002',
            'date_order': now,
        })

        # 3. Past order created 10 days ago
        cls.order_past = cls.env['pos.order'].create({
            'session_id': cls.pos_session.id,
            'partner_id': cls.partner.id,
            'amount_total': 250.0,
            'amount_paid': 250.0,
            'amount_tax': 0.0,
            'amount_return': 0.0,
            'state': 'done',
            'pos_reference': 'POS-REF-003',
            'date_order': ten_days_ago,
        })

        # 4. Cancelled order (should always be filtered out)
        cls.order_cancel = cls.env['pos.order'].create({
            'session_id': cls.pos_session.id,
            'partner_id': cls.partner.id,
            'amount_total': 80.0,
            'amount_paid': 0.0,
            'amount_tax': 0.0,
            'amount_return': 0.0,
            'state': 'cancel',
            'pos_reference': 'POS-REF-004',
            'date_order': now,
        })

    def test_get_all_order_config(self):
        """Test retrieving configuration parameters from ir.config_parameter."""
        self.icp.set_str('pos_all_orders.pos_all_order', 'last_n')
        self.icp.set_int('pos_all_orders.n_days', 7)
        config = self.pos_session_model.get_all_order_config()
        self.assertEqual(config.get('config'), 'last_n')
        self.assertEqual(config.get('n_days'), 7)

        self.icp.set_str('pos_all_orders.pos_all_order', False)
        self.icp.set_int('pos_all_orders.n_days', 0)
        config = self.pos_session_model.get_all_order_config()
        self.assertFalse(config.get('config'))
        self.assertEqual(config.get('n_days'), 0)

    def test_get_all_order_variants(self):
        """Test get_all_order with various input structures and date filters."""
        # Session as dict
        orders_dict = self.pos_session_model.get_all_order({'session': self.pos_session.id})
        order_ids = [o['id'] for o in orders_dict]
        self.assertIn(self.order_paid.id, order_ids)
        self.assertIn(self.order_draft.id, order_ids)
        self.assertNotIn(self.order_cancel.id, order_ids)

        # Verify record dictionary structure
        first_order = next(o for o in orders_dict if o['id'] == self.order_paid.id)
        self.assertEqual(first_order['partner_id'], self.partner.name)
        self.assertEqual(first_order['total'], 120.0)
        self.assertEqual(first_order['pos_reference'], 'POS-REF-001')

        # Order without partner
        draft_order = next(o for o in orders_dict if o['id'] == self.order_draft.id)
        self.assertEqual(draft_order['partner_id'], '')

        # Session as int
        orders_int = self.pos_session_model.get_all_order(self.pos_session.id)
        self.assertEqual(len(orders_int), len(orders_dict))

        # Session as list of dict
        orders_list_dict = self.pos_session_model.get_all_order([{'session': self.pos_session.id}])
        self.assertEqual(len(orders_list_dict), len(orders_dict))

        # Session as list of int
        orders_list_int = self.pos_session_model.get_all_order([self.pos_session.id])
        self.assertEqual(len(orders_list_int), len(orders_dict))

        # Session with n_days filter (e.g. last 5 days - should exclude 10 days ago order)
        orders_recent = self.pos_session_model.get_all_order({
            'session': self.pos_session.id,
            'n_days': 5,
        })
        recent_ids = [o['id'] for o in orders_recent]
        self.assertIn(self.order_paid.id, recent_ids)
        self.assertNotIn(self.order_past.id, recent_ids)
        self.assertNotIn(self.order_cancel.id, recent_ids)

        # Call with None
        orders_none = self.pos_session_model.get_all_order(None)
        self.assertTrue(len(orders_none) >= 3)

    def test_get_all_past_orders(self):
        """Test get_all_past_orders returns valid orders and excludes cancelled."""
        orders = self.pos_session_model.get_all_past_orders(self.pos_session.id)
        order_ids = [o['id'] for o in orders]
        self.assertIn(self.order_paid.id, order_ids)
        self.assertIn(self.order_past.id, order_ids)
        self.assertNotIn(self.order_cancel.id, order_ids)

    def test_get_default_all_orders(self):
        """Test get_default_all_orders retrieves non-cancelled orders."""
        orders = self.pos_session_model.get_default_all_orders(self.pos_session.id)
        order_ids = [o['id'] for o in orders]
        self.assertIn(self.order_paid.id, order_ids)
        self.assertIn(self.order_past.id, order_ids)
        self.assertNotIn(self.order_cancel.id, order_ids)

    def test_get_pos_all_orders_routing(self):
        """Test get_pos_all_orders routing for different configuration options."""
        # 1. Config: current_session
        self.icp.set_str('pos_all_orders.pos_all_order', 'current_session')
        orders = self.pos_session_model.get_pos_all_orders({'session': self.pos_session.id})
        order_ids = [o['id'] for o in orders]
        self.assertIn(self.order_paid.id, order_ids)
        self.assertNotIn(self.order_cancel.id, order_ids)

        # 2. Config: past_order
        self.icp.set_str('pos_all_orders.pos_all_order', 'past_order')
        orders_past = self.pos_session_model.get_pos_all_orders(self.pos_session.id)
        order_past_ids = [o['id'] for o in orders_past]
        self.assertIn(self.order_past.id, order_past_ids)

        # 3. Config: last_n
        self.icp.set_str('pos_all_orders.pos_all_order', 'last_n')
        self.icp.set_int('pos_all_orders.n_days', 3)
        orders_n = self.pos_session_model.get_pos_all_orders([{'session': self.pos_session.id}])
        order_n_ids = [o['id'] for o in orders_n]
        self.assertIn(self.order_paid.id, order_n_ids)
        self.assertNotIn(self.order_past.id, order_n_ids)

        # 4. Default fallback when config is unset
        self.icp.set_str('pos_all_orders.pos_all_order', False)
        orders_default = self.pos_session_model.get_pos_all_orders([self.pos_session.id])
        order_def_ids = [o['id'] for o in orders_default]
        self.assertIn(self.order_paid.id, order_def_ids)
        self.assertNotIn(self.order_cancel.id, order_def_ids)
