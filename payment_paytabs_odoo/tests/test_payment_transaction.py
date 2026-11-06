# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from unittest.mock import patch

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_paytabs_odoo.controllers.payment_paytabs_odoo import PaymentPaytabs
from odoo.addons.payment_paytabs_odoo.tests.common import PaytabsCommon


@tagged('post_install', '-at_install')
class TestPaymentTransaction(PaytabsCommon):

    def test_compute_reference_paytabs(self):
        """ Test that reference prefix is singularized for PayTabs transactions. """
        prefix = self.env['payment.transaction']._compute_reference('paytabs')
        self.assertTrue(prefix.startswith('tx-'))

    def test_compute_reference_other_provider(self):
        """ Test that custom prefix is retained for non-PayTabs providers. """
        reference = self.env['payment.transaction']._compute_reference(
            'none', prefix='INV-2026-001'
        )
        self.assertTrue(reference.startswith('INV-2026-001'))

    def test_get_specific_rendering_values(self):
        """ Test that _get_specific_rendering_values delegates to execute_payment for PayTabs. """
        tx = self._create_transaction(flow='redirect')
        with patch.object(
            type(self.provider), '_paytabs_make_request', return_value=dict(self.redirect_response)
        ):
            rendering_values = tx._get_specific_rendering_values(None)
        self.assertEqual(rendering_values['api_url'], self.redirect_url)
        self.assertEqual(tx.provider_reference, self.tran_ref)

    def test_get_specific_rendering_values_other_provider(self):
        """ Test that _get_specific_rendering_values returns super values for non-PayTabs provider. """
        non_paytabs_tx = self._create_transaction(flow='redirect', provider_id=self.dummy_provider.id)
        with patch.object(type(non_paytabs_tx), 'execute_payment') as mock_execute:
            res = non_paytabs_tx._get_specific_rendering_values(None)
            self.assertEqual(mock_execute.call_count, 0)
            self.assertDictEqual(res, {})

    def test_execute_payment_invalid_profile_key(self):
        """ Test that a non-numeric profile_key raises a ValidationError. """
        tx = self._create_transaction(flow='redirect')
        self.provider.profile_key = 'non_numeric_key'
        with self.assertRaises(ValidationError) as cm:
            tx.execute_payment()
        self.assertIn("PayTabs Profile ID must be numeric", str(cm.exception))

    def test_execute_payment_missing_profile_key(self):
        """ Test that a missing or false profile_key raises a ValidationError. """
        tx = self._create_transaction(flow='redirect')
        self.provider.profile_key = False
        with self.assertRaises(ValidationError) as cm:
            tx.execute_payment()
        self.assertIn("PayTabs Profile ID must be numeric", str(cm.exception))

    def test_execute_payment_payload_and_provider_reference(self):
        """ Test that execute_payment builds the correct payload and sets provider_reference. """
        tx = self._create_transaction(flow='redirect')
        with patch.object(
            type(self.provider), '_paytabs_make_request', return_value=dict(self.redirect_response)
        ) as mock_req:
            res = tx.execute_payment()
            self.assertEqual(mock_req.call_count, 1)
            call_url = mock_req.call_args[0][0]
            call_payload = mock_req.call_args[0][1]
            expect_redirect = mock_req.call_args.kwargs.get('expect_redirect')

            self.assertEqual(call_url, self.provider.domain)
            self.assertTrue(expect_redirect)
            self.assertEqual(call_payload['profile_id'], int(self.provider.profile_key))
            self.assertEqual(call_payload['tran_type'], 'sale')
            self.assertEqual(call_payload['tran_class'], 'ecom')
            self.assertEqual(call_payload['cart_id'], tx.reference)
            self.assertEqual(call_payload['cart_description'], tx.reference)
            self.assertEqual(call_payload['cart_currency'], tx.currency_id.name)
            self.assertEqual(call_payload['cart_amount'], tx.amount)
            self.assertIn(PaymentPaytabs._return_url, call_payload['return'])
            self.assertIn(f"ref={tx.reference}", call_payload['return'])
            self.assertIn(PaymentPaytabs._webhook_url, call_payload['callback'])
            self.assertEqual(call_payload['customer_details']['name'], tx.partner_name)
            self.assertEqual(call_payload['customer_details']['email'], tx.partner_email)
            self.assertEqual(call_payload['shipping_details']['name'], tx.partner_name)

            self.assertEqual(res['api_url'], self.redirect_url)
            self.assertEqual(tx.provider_reference, self.tran_ref)

    def test_extract_reference(self):
        """ Test reference extraction from cartId, cart_id, and ref keys. """
        # Redirect data with cartId
        ref = self.env['payment.transaction']._extract_reference('paytabs', {'cartId': 'REF_123'})
        self.assertEqual(ref, 'REF_123')

        # Webhook data with cart_id
        ref = self.env['payment.transaction']._extract_reference('paytabs', {'cart_id': 'REF_456'})
        self.assertEqual(ref, 'REF_456')

        # Custom return URL parameter with ref
        ref = self.env['payment.transaction']._extract_reference('paytabs', {'ref': 'REF_789'})
        self.assertEqual(ref, 'REF_789')

    @mute_logger('odoo.addons.payment_paytabs_odoo.models.payment_transaction')
    def test_extract_reference_missing(self):
        """ Test that missing reference in payment data returns None without raising an error. """
        ref = self.env['payment.transaction']._extract_reference('paytabs', {'unrelated': 'data'})
        self.assertIsNone(ref)

    def test_extract_reference_other_provider(self):
        """ Test that reference extraction delegates to super for other providers. """
        ref = self.env['payment.transaction']._extract_reference(
            'none', {'reference': 'TX_SUPER'}
        )
        self.assertEqual(ref, 'TX_SUPER')

    def test_extract_amount_data_paytabs(self):
        """ Test that amount validation is skipped by returning None for PayTabs. """
        tx = self._create_transaction(flow='redirect')
        self.assertIsNone(tx._extract_amount_data({'amount': 100}))

    def test_extract_amount_data_other_provider(self):
        """ Test that _extract_amount_data delegates to super for non-PayTabs providers. """
        non_paytabs_tx = self._create_transaction(flow='redirect', provider_id=self.dummy_provider.id)
        res = non_paytabs_tx._extract_amount_data({'amount': 100})
        self.assertIsNotNone(res)

    def test_apply_updates_authorized_resp_status(self):
        """ Test that respStatus 'A' updates transaction state to 'done'. """
        tx = self._create_transaction(flow='redirect')
        tx._apply_updates({'respStatus': 'A'})
        self.assertEqual(tx.state, 'done')
        self.assertEqual(tx.state_message, 'Authorised')

    def test_apply_updates_authorized_resp_status_word(self):
        """ Test that respStatus 'Authorized' updates transaction state to 'done'. """
        tx = self._create_transaction(flow='redirect')
        tx._apply_updates({'respStatus': 'Authorized'})
        self.assertEqual(tx.state, 'done')
        self.assertEqual(tx.state_message, 'Authorised')

    def test_apply_updates_webhook_response_status_authorized(self):
        """ Test that payment_result with response_status 'A' updates transaction state to 'done'. """
        tx = self._create_transaction(flow='redirect')
        tx._apply_updates(self.webhook_data_authorized)
        self.assertEqual(tx.state, 'done')
        self.assertEqual(tx.state_message, 'Authorised')

    def test_apply_updates_pending_statuses(self):
        """ Test that pending statuses update transaction state to 'pending'. """
        pending_statuses = ('APPROVED', 'H', 'Hold', 'P', 'Pending')
        for status in pending_statuses:
            tx = self._create_transaction(
                flow='redirect', reference=f'{self.reference}_pending_{status}'
            )
            tx._apply_updates({'respStatus': status})
            self.assertEqual(tx.state, 'pending', f"Status '{status}' should set state to 'pending'")

    def test_apply_updates_canceled_statuses(self):
        """ Test that error/canceled statuses update transaction state to 'cancel'. """
        canceled_statuses = ('C', 'E', 'D', 'Declined', 'Error')
        for status in canceled_statuses:
            tx = self._create_transaction(
                flow='redirect', reference=f'{self.reference}_cancel_{status}'
            )
            tx._apply_updates({'respStatus': status})
            self.assertEqual(tx.state, 'cancel', f"Status '{status}' should set state to 'cancel'")

    @mute_logger('odoo.addons.payment_paytabs_odoo.models.payment_transaction')
    def test_apply_updates_unrecognized_status(self):
        """ Test that an unrecognized status sets transaction state to 'error'. """
        tx = self._create_transaction(flow='redirect')
        tx._apply_updates({'respStatus': 'UNKNOWN_STATUS'})
        self.assertEqual(tx.state, 'error')

    def test_apply_updates_status_missing_queries_api(self):
        """ Test that when status is missing from payment data, PayTabs query API is polled. """
        tx = self._create_transaction(flow='redirect')
        tx.provider_reference = self.tran_ref
        query_response = {
            'payment_result': {
                'response_status': 'A',
                'response_message': 'Authorised',
            }
        }
        with patch.object(
            type(self.provider), '_paytabs_make_request', return_value=query_response
        ) as mock_query:
            tx._apply_updates({'cartId': tx.reference})
            self.assertEqual(mock_query.call_count, 1)
            query_url, query_payload = mock_query.call_args[0][:2]
            self.assertIn('/payment/query', query_url)
            self.assertEqual(query_payload['profile_id'], int(self.provider.profile_key))
            self.assertEqual(query_payload['tran_ref'], self.tran_ref)
            self.assertEqual(tx.state, 'done')

    @mute_logger('odoo.addons.payment_paytabs_odoo.models.payment_transaction')
    def test_apply_updates_status_missing_api_query_fails(self):
        """ Test that API query exception when status is missing does not crash and marks error. """
        tx = self._create_transaction(flow='redirect')
        tx.provider_reference = self.tran_ref
        with patch.object(
            type(self.provider), '_paytabs_make_request', side_effect=Exception("API failure")
        ):
            tx._apply_updates({'cartId': tx.reference})
            self.assertEqual(tx.state, 'error')

    def test_search_by_reference(self):
        """ Test that transactions can be retrieved by reference from PayTabs notification data. """
        tx = self._create_transaction(flow='redirect')

        # By cartId
        found_tx = self.env['payment.transaction']._search_by_reference(
            'paytabs', {'cartId': tx.reference}
        )
        self.assertEqual(found_tx, tx)

        # By cart_id
        found_tx = self.env['payment.transaction']._search_by_reference(
            'paytabs', {'cart_id': tx.reference}
        )
        self.assertEqual(found_tx, tx)

        # By ref
        found_tx = self.env['payment.transaction']._search_by_reference(
            'paytabs', {'ref': tx.reference}
        )
        self.assertEqual(found_tx, tx)

