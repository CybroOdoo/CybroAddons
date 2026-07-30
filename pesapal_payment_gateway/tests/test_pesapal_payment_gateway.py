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
import json
import uuid
from unittest.mock import patch

import requests

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


class MockResponse:
    """Lightweight stand-in for `requests.Response` used to drive the
    branches of the Pesapal integration without hitting the network."""

    def __init__(self, json_data=None, raise_exc=None):
        self._json_data = json_data or {}
        self._raise_exc = raise_exc

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self._raise_exc:
            raise self._raise_exc


@tagged('post_install', '-at_install')
class TestPesapalPaymentTransaction(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.currency = cls.env.company.currency_id
        cls.partner = cls.env['res.partner'].create({
            'name': 'Pesapal Test Customer',
            'email': 'pesapal.customer@example.com',
            'phone': '+254712345678',
            'street': 'Test Street',
            'city': 'Nairobi',
            'zip': '00100',
            'country_id': cls.env.ref('base.ke').id,
        })
        cls.provider = cls.env['payment.provider'].create({
            'name': 'Pesapal Test Provider',
            'code': 'pesapal',
            'state': 'test',
            'pesapal_consumer_key': 'test_consumer_key',
            'pesapal_consumer_secret': 'test_consumer_secret',
        })

    def _create_transaction(self, **extra_vals):
        vals = {
            'provider_id': self.provider.id,
            'payment_method_id': self.env.ref(
                'payment.payment_method_unknown').id,
            'reference': 'PESAPAL-TEST-%s' % uuid.uuid4().hex[:12],
            'amount': 100.0,
            'currency_id': self.currency.id,
            'partner_id': self.partner.id,
        }
        vals.update(extra_vals)
        return self.env['payment.transaction'].create(vals)

    # ------------------------------------------------------------------
    # authenticate_payment
    # ------------------------------------------------------------------
    def test_authenticate_payment_success(self):
        """A successful token request should return the access token."""
        tx = self._create_transaction()
        with patch(
            'odoo.addons.pesapal_payment_gateway.models.payment_transaction'
            '.requests.post',
            return_value=MockResponse({'token': 'fake-access-token'}),
        ):
            token = tx.authenticate_payment()
        self.assertEqual(token, 'fake-access-token')

    def test_authenticate_payment_failure(self):
        """Any network/HTTP error while requesting the token should be
        swallowed and return None rather than raising."""
        tx = self._create_transaction()
        with patch(
            'odoo.addons.pesapal_payment_gateway.models.payment_transaction'
            '.requests.post',
            side_effect=requests.exceptions.RequestException('boom'),
        ):
            token = tx.authenticate_payment()
        self.assertIsNone(token)

    # ------------------------------------------------------------------
    # _get_specific_rendering_values
    # ------------------------------------------------------------------
    def test_get_specific_rendering_values_ignores_other_providers(self):
        """Non-pesapal transactions must not trigger the Pesapal
        authentication/IPN flow at all."""
        other_provider = self.env['payment.provider'].create({
            'name': 'Manual Test Provider 2',
            'code': 'none',
            'state': 'test',
        })
        tx = self._create_transaction(provider_id=other_provider.id)
        with patch.object(type(tx), 'authenticate_payment') as mock_auth:
            tx._get_specific_rendering_values({})
        mock_auth.assert_not_called()

    def test_get_specific_rendering_values_auth_failure_returns_super(self):
        """If we cannot obtain an access token, fall back to the base
        rendering values instead of raising."""
        tx = self._create_transaction()
        with patch.object(
            type(tx), 'authenticate_payment', return_value=None
        ), patch.object(
            type(tx), '_pesapal_register_ipn_url'
        ) as mock_register:
            result = tx._get_specific_rendering_values({})
        mock_register.assert_not_called()
        self.assertIsInstance(result, dict)

    def test_get_specific_rendering_values_success_chain(self):
        """When a token is obtained, the IPN registration step should be
        invoked and its result returned."""
        tx = self._create_transaction()
        expected = {'api_url': '/payment/pesapal/response', 'data': {},
                    'token': 'tok-123'}
        with patch.object(
            type(tx), 'authenticate_payment', return_value='tok-123'
        ), patch.object(
            type(tx), '_pesapal_register_ipn_url', return_value=expected
        ) as mock_register:
            result = tx._get_specific_rendering_values({})
        mock_register.assert_called_once_with(token='tok-123')
        self.assertEqual(result, expected)

    # ------------------------------------------------------------------
    # _pesapal_register_ipn_url
    # ------------------------------------------------------------------
    def test_pesapal_register_ipn_url_success(self):
        """A successful IPN registration should hand off to the order
        submission step with the returned ipn_id."""
        tx = self._create_transaction()
        with patch(
            'odoo.addons.pesapal_payment_gateway.models.payment_transaction'
            '.requests.post',
            return_value=MockResponse({'ipn_id': 'ipn-999'}),
        ), patch.object(
            type(tx), '_pesapal_submit_order_request', return_value='submitted'
        ) as mock_submit:
            result = tx._pesapal_register_ipn_url(token='tok-123')
        self.assertEqual(result, 'submitted')
        _, kwargs = mock_submit.call_args
        self.assertEqual(kwargs.get('token'), 'tok-123')
        self.assertEqual(kwargs.get('ipn_id'), 'ipn-999')

    def test_pesapal_register_ipn_url_failure_returns_none(self):
        """A failed IPN registration request must not raise and must
        return None without attempting to submit the order."""
        tx = self._create_transaction()
        with patch(
            'odoo.addons.pesapal_payment_gateway.models.payment_transaction'
            '.requests.post',
            side_effect=requests.exceptions.RequestException('boom'),
        ), patch.object(
            type(tx), '_pesapal_submit_order_request'
        ) as mock_submit:
            result = tx._pesapal_register_ipn_url(token='tok-123')
        self.assertIsNone(result)
        mock_submit.assert_not_called()

    # ------------------------------------------------------------------
    # _pesapal_submit_order_request
    # ------------------------------------------------------------------
    def test_submit_order_request_missing_phone_raises(self):
        """A partner without a phone number must not reach Pesapal."""
        partner_no_phone = self.env['res.partner'].create({
            'name': 'No Phone Customer',
            'email': 'nophone@example.com',
        })
        tx = self._create_transaction(partner_id=partner_no_phone.id)
        with self.assertRaises(ValueError):
            tx._pesapal_submit_order_request(
                token='tok-123', odoo_base_url='https://example.com',
                ipn_id='ipn-999')

    def test_submit_order_request_strips_country_code_and_plus(self):
        """The leading '+' and the partner's country calling code should be
        stripped from the phone number sent to Pesapal."""
        tx = self._create_transaction()
        captured = {}

        def fake_post(url, headers=None, data=None, timeout=None):
            captured['url'] = url
            captured['data'] = data
            return MockResponse({
                'order_tracking_id': 'track-1',
                'redirect_url': 'https://pesapal.example/redirect',
            })

        with patch(
            'odoo.addons.pesapal_payment_gateway.models.payment_transaction'
            '.requests.post',
            side_effect=fake_post,
        ):
            result = tx._pesapal_submit_order_request(
                token='tok-123', odoo_base_url='https://example.com',
                ipn_id='ipn-999')

        sent_payload = json.loads(captured['data'])
        self.assertEqual(
            sent_payload['billing_address']['phone_number'], '712345678')
        self.assertEqual(result['data']['order_tracking_id'], 'track-1')
        self.assertEqual(
            result['data']['redirect_url'], 'https://pesapal.example/redirect')
        self.assertEqual(result['token'], 'tok-123')
        self.assertEqual(tx.provider_reference, sent_payload['id'])

    def test_submit_order_request_failure_returns_none(self):
        """A failed order submission request should return None instead of
        raising, leaving provider_reference untouched."""
        tx = self._create_transaction()
        with patch(
            'odoo.addons.pesapal_payment_gateway.models.payment_transaction'
            '.requests.post',
            side_effect=requests.exceptions.RequestException('boom'),
        ):
            result = tx._pesapal_submit_order_request(
                token='tok-123', odoo_base_url='https://example.com',
                ipn_id='ipn-999')
        self.assertIsNone(result)
        self.assertFalse(tx.provider_reference)

    # ------------------------------------------------------------------
    # _get_tx_from_notification_data
    # ------------------------------------------------------------------
    def test_get_tx_from_notification_data_missing_reference_raises(self):
        tx = self._create_transaction()
        with self.assertRaises(ValidationError):
            self.env['payment.transaction']._get_tx_from_notification_data(
                'pesapal', {})

    def test_get_tx_from_notification_data_found_by_provider_reference(self):
        tx = self._create_transaction()
        tx.provider_reference = 'order-uuid-123'
        found = self.env['payment.transaction']._get_tx_from_notification_data(
            'pesapal', {'OrderMerchantReference': 'order-uuid-123'})
        self.assertEqual(found, tx)

    def test_get_tx_from_notification_data_found_by_reference_fallback(self):
        tx = self._create_transaction()
        found = self.env['payment.transaction']._get_tx_from_notification_data(
            'pesapal', {'OrderMerchantReference': tx.reference})
        self.assertEqual(found, tx)

    def test_get_tx_from_notification_data_not_found_raises(self):
        self._create_transaction()
        with self.assertRaises(ValidationError):
            self.env['payment.transaction']._get_tx_from_notification_data(
                'pesapal', {'OrderMerchantReference': 'does-not-exist'})

    # ------------------------------------------------------------------
    # _process_notification_data
    # ------------------------------------------------------------------
    def _process_with_status(self, tx, payment_status, error_code=None,
                              order_tracking_id='track-1', auth_token='tok-123'):
        response_data = {'payment_status_description': payment_status}
        if error_code:
            response_data['error'] = {'code': error_code}
        with patch.object(
            type(tx), 'authenticate_payment', return_value=auth_token
        ), patch(
            'odoo.addons.pesapal_payment_gateway.models.payment_transaction'
            '.requests.get',
            return_value=MockResponse(response_data),
        ):
            tx._process_notification_data(
                {'OrderTrackingId': order_tracking_id,
                 'OrderMerchantReference': tx.reference})

    def test_process_notification_data_completed_sets_done(self):
        tx = self._create_transaction()
        self._process_with_status(tx, 'Completed')
        self.assertEqual(tx.state, 'done')

    def test_process_notification_data_failed_sets_canceled(self):
        tx = self._create_transaction()
        self._process_with_status(tx, 'Failed')
        self.assertEqual(tx.state, 'cancel')

    def test_process_notification_data_reversed_sets_canceled(self):
        tx = self._create_transaction()
        self._process_with_status(tx, 'Reversed')
        self.assertEqual(tx.state, 'cancel')

    def test_process_notification_data_invalid_payment_details_not_found_pending(self):
        tx = self._create_transaction()
        self._process_with_status(
            tx, 'Invalid', error_code='payment_details_not_found')
        self.assertEqual(tx.state, 'pending')

    def test_process_notification_data_invalid_other_error_sets_canceled(self):
        tx = self._create_transaction()
        self._process_with_status(
            tx, 'Invalid', error_code='some_other_error')
        self.assertEqual(tx.state, 'cancel')

    def test_process_notification_data_unknown_status_sets_pending(self):
        tx = self._create_transaction()
        self._process_with_status(tx, 'Pending')
        self.assertEqual(tx.state, 'pending')

    def test_process_notification_data_auth_failure_sets_error(self):
        tx = self._create_transaction()
        with patch.object(
            type(tx), 'authenticate_payment', return_value=None
        ):
            tx._process_notification_data(
                {'OrderTrackingId': 'track-1',
                 'OrderMerchantReference': tx.reference})
        self.assertEqual(tx.state, 'error')

    def test_process_notification_data_missing_tracking_id_sets_error(self):
        tx = self._create_transaction()
        with patch.object(
            type(tx), 'authenticate_payment', return_value='tok-123'
        ):
            tx._process_notification_data(
                {'OrderMerchantReference': tx.reference})
        self.assertEqual(tx.state, 'error')

    def test_process_notification_data_status_request_exception_sets_error(self):
        tx = self._create_transaction()
        with patch.object(
            type(tx), 'authenticate_payment', return_value='tok-123'
        ), patch(
            'odoo.addons.pesapal_payment_gateway.models.payment_transaction'
            '.requests.get',
            side_effect=requests.exceptions.RequestException('boom'),
        ):
            tx._process_notification_data(
                {'OrderTrackingId': 'track-1',
                 'OrderMerchantReference': tx.reference})
        self.assertEqual(tx.state, 'error')

    def test_process_notification_data_ignores_other_providers(self):
        """Transactions on a non-pesapal provider must be left untouched by
        this override (no requests should be made)."""
        other_provider = self.env['payment.provider'].create({
            'name': 'Manual Test Provider',
            'code': 'none',
            'state': 'test',
        })
        tx = self._create_transaction(provider_id=other_provider.id)
        with patch(
            'odoo.addons.pesapal_payment_gateway.models.payment_transaction'
            '.requests.get'
        ) as mock_get:
            tx._process_notification_data(
                {'OrderMerchantReference': tx.reference})
        mock_get.assert_not_called()