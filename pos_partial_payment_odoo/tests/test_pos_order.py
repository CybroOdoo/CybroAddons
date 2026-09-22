# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (odoo@cybrosys.info)
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
################################################################################
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.addons.point_of_sale.models.pos_order import PosOrder as BasePosOrder
from odoo.tests import TransactionCase


class TestPosOrder(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.payment_method = cls.env['pos.payment.method'].create({
            'name': 'Test Pay Later',
            'company_id': cls.env.company.id,
        })
        cls.config = cls.env['pos.config'].create({
            'name': 'Partial Payment Test Config',
            'company_id': cls.env.company.id,
            'partial_payment': True,
            'payment_method_ids': [(6, 0, cls.payment_method.ids)],
        })

    def setUp(self):
        super().setUp()
        self.config = self.__class__.config

    def open_new_session(self):
        session = self.config.current_session_id
        if not session:
            session = self.env['pos.session'].create({
                'config_id': self.config.id,
                'user_id': self.env.uid,
                'state': 'opened',
            })
        elif session.state != 'opened':
            session.write({'state': 'opened'})
        return session

    def _create_basic_order(self, **extra_vals):
        if not self.config.current_session_id:
            self.open_new_session()
        vals = {
            'name': extra_vals.pop('name', 'Partial Payment Test Order'),
            'company_id': self.env.company.id,
            'session_id': self.config.current_session_id.id,
            'config_id': self.config.id,
            'pricelist_id': self.config.pricelist_id.id,
            'amount_tax': 0.0,
            'amount_total': 100.0,
            'amount_paid': 0.0,
            'amount_return': 0.0,
        }
        vals.update(extra_vals)
        return self.env['pos.order'].create(vals)

    def test_compute_due_amount_uses_paid_amount(self):
        order = self._create_basic_order(amount_total=100.0, amount_paid=35.0)

        order._compute_due_amount()

        self.assertEqual(order.due_amount, 65.0)

    def test_order_fields_includes_partial_payment_flag(self):
        ui_order = {'is_partial_payment': True}

        with patch.object(BasePosOrder, '_order_fields', return_value={}, create=True):
            vals = self.env['pos.order']._order_fields(ui_order)

        self.assertTrue(vals['is_partial_payment'])

    def test_action_pos_order_paid_allows_underpaid_order_when_enabled(self):
        self.config.partial_payment = True
        order = self._create_basic_order(amount_total=100.0, amount_paid=25.0)

        result = order.action_pos_order_paid()

        self.assertTrue(result)
        self.assertEqual(order.state, 'paid')

    def test_action_pos_order_paid_blocks_underpaid_order_when_disabled(self):
        self.env['pos.config'].search([]).write({'partial_payment': False})
        order = self._create_basic_order(amount_total=100.0, amount_paid=25.0)

        with self.assertRaises(UserError):
            order.action_pos_order_paid()

    def test_search_partial_order_ids_returns_matching_partial_orders(self):
        partial_order = self._create_basic_order(
            name='Partial Order',
            is_partial_payment=True,
            state='paid',
        )
        self._create_basic_order(
            name='Regular Order',
            is_partial_payment=False,
            state='paid',
        )

        result = self.env['pos.order'].search_partial_order_ids(
            self.config.id,
            [],
            10,
            0,
        )

        self.assertEqual(result['totalCount'], 1)
        self.assertEqual(result['orders'][0][0], partial_order.id)
        self.assertIsInstance(result['orders'][0][1], str)
