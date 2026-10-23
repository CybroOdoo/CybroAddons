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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from datetime import date, timedelta
from unittest.mock import patch

from odoo.fields import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestCancelQuotationExpiry(TransactionCase):
    """Test cases for cancelling expired sales quotations."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env['res.partner']
        cls.Product = cls.env['product.product']
        cls.SaleOrder = cls.env['sale.order']

        cls.partner = cls.Partner.create({
            'name': 'Test Customer',
            'email': 'customer@test.com',
        })

        cls.product = cls.Product.create({
            'name': 'Test Product',
            'type': 'consu',
            'list_price': 100.0,
        })

    def _create_order(self, state='draft', validity_date=None):
        """Helper to create sale orders in specific states and validity dates."""
        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
            'validity_date': validity_date,
            'order_line': [Command.create({
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
            })],
        })
        if state == 'sent':
            order.write({'state': 'sent'})
        elif state == 'sale':
            order.action_confirm()
        elif state == 'cancel':
            order._action_cancel()
        return order

    def test_cancel_expired_quotation_in_draft_state(self):
        """Test that a draft quotation with validity_date in the past is cancelled."""
        past_date = date.today() - timedelta(days=1)
        order = self._create_order(state='draft', validity_date=past_date)
        self.assertEqual(order.state, 'draft')

        self.SaleOrder.cancel_expired_quotation()
        self.assertEqual(
            order.state,
            'cancel',
            "Quotation in draft state with past validity date should be cancelled."
        )

    def test_cancel_expired_quotation_in_sent_state(self):
        """Test that a sent quotation with validity_date in the past is cancelled."""
        past_date = date.today() - timedelta(days=3)
        order = self._create_order(state='sent', validity_date=past_date)
        self.assertEqual(order.state, 'sent')

        self.SaleOrder.cancel_expired_quotation()
        self.assertEqual(
            order.state,
            'cancel',
            "Quotation in sent state with past validity date should be cancelled."
        )

    def test_quotation_with_future_validity_date_not_cancelled(self):
        """Test that draft and sent quotations with future validity dates are not cancelled."""
        future_date = date.today() + timedelta(days=5)
        draft_order = self._create_order(state='draft', validity_date=future_date)
        sent_order = self._create_order(state='sent', validity_date=future_date)

        self.SaleOrder.cancel_expired_quotation()
        self.assertEqual(
            draft_order.state,
            'draft',
            "Draft quotation with future validity date should remain in draft state."
        )
        self.assertEqual(
            sent_order.state,
            'sent',
            "Sent quotation with future validity date should remain in sent state."
        )

    def test_quotation_with_today_validity_date_not_cancelled(self):
        """Test that quotation with validity_date equal to today is not cancelled."""
        today_date = date.today()
        order = self._create_order(state='draft', validity_date=today_date)

        self.SaleOrder.cancel_expired_quotation()
        self.assertEqual(
            order.state,
            'draft',
            "Quotation expiring today should not be cancelled until tomorrow."
        )

    def test_quotation_without_validity_date_not_cancelled(self):
        """Test that a quotation without a validity date (validity_date=False) is not cancelled."""
        order = self._create_order(state='draft', validity_date=False)

        self.SaleOrder.cancel_expired_quotation()
        self.assertEqual(
            order.state,
            'draft',
            "Quotation without a validity date should not be cancelled."
        )

    def test_confirmed_sale_order_not_cancelled(self):
        """Test that confirmed orders (state='sale') with past validity date are not cancelled."""
        past_date = date.today() - timedelta(days=2)
        order = self._create_order(state='draft', validity_date=past_date)
        order.action_confirm()
        self.assertEqual(order.state, 'sale')

        self.SaleOrder.cancel_expired_quotation()
        self.assertEqual(
            order.state,
            'sale',
            "Confirmed sale order with past validity date must not be cancelled."
        )

    def test_batch_cancellation_of_mixed_orders(self):
        """Test processing multiple quotations with mixed states and validity dates in batch."""
        past_date = date.today() - timedelta(days=4)
        future_date = date.today() + timedelta(days=4)

        expired_draft_1 = self._create_order(state='draft', validity_date=past_date)
        expired_draft_2 = self._create_order(state='draft', validity_date=past_date)
        expired_sent = self._create_order(state='sent', validity_date=past_date)
        active_draft = self._create_order(state='draft', validity_date=future_date)
        no_date_draft = self._create_order(state='draft', validity_date=False)

        self.SaleOrder.cancel_expired_quotation()

        self.assertEqual(expired_draft_1.state, 'cancel')
        self.assertEqual(expired_draft_2.state, 'cancel')
        self.assertEqual(expired_sent.state, 'cancel')
        self.assertEqual(active_draft.state, 'draft')
        self.assertEqual(no_date_draft.state, 'draft')

    def test_email_notification_sent_on_cancellation(self):
        """Test that cancellation email template is triggered with correct parameters."""
        past_date = date.today() - timedelta(days=1)
        order = self._create_order(state='draft', validity_date=past_date)

        template = self.env.ref('sale.mail_template_sale_cancellation', raise_if_not_found=False)
        if template:
            with patch.object(type(template), 'send_mail') as mock_send_mail:
                self.SaleOrder.cancel_expired_quotation()
                mock_send_mail.assert_called_with(
                    order.id,
                    force_send=True,
                    raise_exception=False,
                )
        else:
            self.SaleOrder.cancel_expired_quotation()

        self.assertEqual(order.state, 'cancel')

    def test_cancellation_when_template_missing(self):
        """Test cancellation logic works gracefully even when email template is not found."""
        past_date = date.today() - timedelta(days=1)
        order = self._create_order(state='draft', validity_date=past_date)

        with patch.object(type(self.env), 'ref', return_value=False):
            self.SaleOrder.cancel_expired_quotation()

        self.assertEqual(
            order.state,
            'cancel',
            "Quotation should still be cancelled even if email template is missing."
        )

    def test_cron_record_definition_and_execution(self):
        """Test that the scheduled action XML record is defined and executes properly."""
        cron = self.env.ref(
            'cancel_quotation_expiry.ir_cron_expired_quotation_scheduler_action',
            raise_if_not_found=False,
        )
        self.assertTrue(cron, "Cron record ir_cron_expired_quotation_scheduler_action should exist.")
        self.assertEqual(cron.model_id.model, 'sale.order')
        self.assertEqual(cron.code, 'model.cancel_expired_quotation()')
        self.assertEqual(cron.interval_number, 1)
        self.assertEqual(cron.interval_type, 'days')

        # Test execution via cron server action
        past_date = date.today() - timedelta(days=2)
        order = self._create_order(state='draft', validity_date=past_date)
        cron.ir_actions_server_id.run()
        self.assertEqual(
            order.state,
            'cancel',
            "Quotation should be cancelled when the scheduled action is triggered."
        )
