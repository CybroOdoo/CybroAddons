# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from datetime import timedelta

from odoo import fields
from odoo.addons.point_of_sale.tests.common import TestPoSCommon
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestPosSessionAllOrders(TestPoSCommon):

    def setUp(self):
        super().setUp()
        self.config = self.basic_config
        self.session = self.open_new_session()
        self.other_currency_config.open_ui()
        self.other_session = self.other_currency_config.current_session_id
        self.other_session.set_opening_control(0, None)
        self.product = self.create_product(
            'POS All Orders Test Product',
            self.categ_basic,
            10.0,
        )
        self.partner = self.env['res.partner'].create({
            'name': 'POS All Orders Test Partner',
        })

    def _create_order(self, session, name, date_order=None, state='paid'):
        return self.env['pos.order'].create({
            'company_id': self.env.company.id,
            'session_id': session.id,
            'partner_id': self.partner.id,
            'name': name,
            'date_order': date_order or fields.Datetime.now(),
            'pos_reference': name,
            'lines': [(0, 0, {
                'name': name,
                'product_id': self.product.id,
                'price_unit': 10.0,
                'discount': 0.0,
                'qty': 1.0,
                'tax_ids': False,
                'price_subtotal': 10.0,
                'price_subtotal_incl': 10.0,
            })],
            'amount_tax': 0.0,
            'amount_total': 10.0,
            'amount_paid': 10.0,
            'amount_return': 0.0,
            'state': state,
        })

    def _result_by_id(self, results):
        return {result['id']: result for result in results}

    def test_get_all_order_config_returns_parameters(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'pos_all_orders.pos_all_order', 'last_n'
        )
        self.env['ir.config_parameter'].sudo().set_param(
            'pos_all_orders.n_days', 5
        )

        config = self.env['pos.session'].get_all_order_config()

        self.assertEqual(config['config'], 'last_n')
        self.assertEqual(config['n_days'], '5')

    def test_get_all_order_returns_orders_for_current_session(self):
        current_order = self._create_order(
            self.session,
            'POSALL-CURRENT-ORDER',
        )
        other_order = self._create_order(
            self.other_session,
            'POSALL-OTHER-ORDER',
        )

        results = self.env['pos.session'].get_all_order({
            'session': self.session.id,
        })
        result_by_id = self._result_by_id(results)

        self.assertIn(current_order.id, result_by_id)
        self.assertNotIn(other_order.id, result_by_id)
        self.assertEqual(result_by_id[current_order.id]['name'], current_order.name)
        self.assertEqual(result_by_id[current_order.id]['pos_reference'], current_order.pos_reference)
        self.assertEqual(result_by_id[current_order.id]['partner_id'], self.partner.name)
        self.assertEqual(result_by_id[current_order.id]['session'], 'current_session')

    def test_get_all_order_returns_orders_for_last_n_days(self):
        now = fields.Datetime.now()
        recent_order = self._create_order(
            self.session,
            'POSALL-RECENT-ORDER',
            date_order=now - timedelta(days=1),
        )
        old_order = self._create_order(
            self.session,
            'POSALL-OLD-ORDER',
            date_order=now - timedelta(days=10),
        )

        results = self.env['pos.session'].get_all_order({'n_days': 3})
        result_by_id = self._result_by_id(results)

        self.assertIn(recent_order.id, result_by_id)
        self.assertNotIn(old_order.id, result_by_id)
        self.assertEqual(result_by_id[recent_order.id]['session'], 'current_session')

    def test_get_all_past_orders_excludes_draft_cancel_and_future_orders(self):
        now = fields.Datetime.now()
        paid_order = self._create_order(
            self.session,
            'POSALL-PAID-PAST-ORDER',
            date_order=now - timedelta(days=1),
            state='paid',
        )
        draft_order = self._create_order(
            self.session,
            'POSALL-DRAFT-PAST-ORDER',
            date_order=now - timedelta(days=1),
            state='draft',
        )
        cancel_order = self._create_order(
            self.session,
            'POSALL-CANCEL-PAST-ORDER',
            date_order=now - timedelta(days=1),
            state='cancel',
        )
        future_order = self._create_order(
            self.session,
            'POSALL-FUTURE-ORDER',
            date_order=now + timedelta(days=1),
            state='paid',
        )

        results = self.env['pos.session'].get_all_past_orders({})
        result_by_id = self._result_by_id(results)

        self.assertIn(paid_order.id, result_by_id)
        self.assertNotIn(draft_order.id, result_by_id)
        self.assertNotIn(cancel_order.id, result_by_id)
        self.assertNotIn(future_order.id, result_by_id)
        self.assertEqual(result_by_id[paid_order.id]['session'], 'past_order')

    def test_get_default_all_orders_returns_session_name(self):
        order = self._create_order(
            self.session,
            'POSALL-DEFAULT-ORDER',
        )

        results = self.env['pos.session'].get_default_all_orders({})
        result_by_id = self._result_by_id(results)

        self.assertIn(order.id, result_by_id)
        self.assertEqual(result_by_id[order.id]['session'], self.session.name)
        self.assertEqual(result_by_id[order.id]['partner_id'], self.partner.name)
