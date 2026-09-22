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

from odoo.addons.account.wizard.account_payment_register import (
    AccountPaymentRegister as BaseAccountPaymentRegister,
)
from odoo.tests import TransactionCase


class TestAccountPaymentRegister(TransactionCase):

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

    def test_action_create_payments_clears_partial_payment_on_invoiced_order(self):
        session = self.open_new_session()
        order = self._create_basic_order(
            session_id=session.id,
            state='paid',
            is_partial_payment=True,
        )
        self.env.cr.execute(
            "UPDATE pos_order SET state = %s WHERE id = %s",
            ('invoiced', order.id),
        )
        order.invalidate_recordset(['state'])
        wizard = self.env['account.payment.register']

        with patch.object(
            BaseAccountPaymentRegister,
            'action_create_payments',
            return_value={'type': 'ir.actions.act_window_close'},
        ):
            result = wizard.action_create_payments()

        self.assertEqual(result, {'type': 'ir.actions.act_window_close'})
        self.assertFalse(order.is_partial_payment)
