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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import sys
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

from odoo import http
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.myfatoorah_payment_gateway.controllers.myfatoorah_payment_gateway import (
    PaymentMyFatoorahController,
)
from odoo.addons.payment.tests.common import PaymentCommon


@contextmanager
def mock_request(env, session=None):
    """Context manager to bind request in Odoo 20 contextvars."""
    mock = MagicMock()
    mock.env = env
    mock.session = session or {}
    mock.website = None
    mock.render.return_value = '<html>Content</html>'
    mock.redirect.side_effect = lambda url: http.Response(status=303)
    token = http.request_var.set(mock)
    try:
        yield mock
    finally:
        http.request_var.reset(token)


@tagged('post_install', '-at_install')
class TestMyFatoorah(PaymentCommon):

    @classmethod
    def setUpClass(cls):
        email_mod = sys.modules.get('odoo.addons.email_id_validation.models.res_partner')
        if email_mod:
            if hasattr(email_mod, 'validate_email'):
                patcher = patch.object(email_mod, 'validate_email', return_value=True)
                patcher.start()
                cls.addClassCleanup(patcher.stop)
            if hasattr(email_mod, 'ResPartner') and hasattr(email_mod.ResPartner, '_check_email'):
                patcher2 = patch.object(email_mod.ResPartner, '_check_email', lambda self: True)
                patcher2.start()
                cls.addClassCleanup(patcher2.stop)
        super().setUpClass()
        if hasattr(cls.env['res.partner'], '_check_email'):
            patcher3 = patch.object(type(cls.env['res.partner']), '_check_email', lambda self: True)
            patcher3.start()
            cls.addClassCleanup(patcher3.stop)
        cls.myfatoorah = cls._prepare_provider(
            "myfatoorah",
            update_values={
                "myfatoorah_token": "dummy_test_token_12345",
                "is_live": False,
            },
        )
        cls.provider = cls.myfatoorah
        cls.currency = cls.currency_usd
        cls.partner = cls.default_partner
        cls.partner.country_id = cls.country_belgium
        cls.partner.phone = "+32 470 12 34 56"
        cls.partner.email = "norbert.buyer@example.com"
        cls.amount = 50.0

        cls.payment_method = cls.env.ref("myfatoorah_payment_gateway.payment_method_myfatoorah")
        cls.payment_method_id = cls.payment_method.id

    def test_01_provider_methods(self):
        """Test provider helper methods and URLs."""
        self.assertEqual(self.provider._get_default_payment_method_codes(), {'myfatoorah'})
        self.assertIn("apitest.myfatoorah.com", self.provider._myfatoorah_get_api_url())

        self.provider.is_live = True
        self.assertIn("api.myfatoorah.com", self.provider._myfatoorah_get_api_url())
        self.provider.is_live = False

    def test_02_get_payment_status(self):
        """Test _myfatoorah_get_payment_status handling of various responses."""
        # Missing token
        self.provider.myfatoorah_token = False
        with self.assertRaises(ValidationError):
            self.provider._myfatoorah_get_payment_status("12345")
        self.provider.myfatoorah_token = "dummy_test_token_12345"

        # Invalid JSON response
        with patch('requests.request') as mock_req:
            mock_req.return_value.status_code = 500
            mock_req.return_value.text = "Internal Server Error"
            mock_req.return_value.json.side_effect = ValueError("Invalid JSON")
            with self.assertRaises(ValidationError):
                self.provider._myfatoorah_get_payment_status("12345")

        # Unsuccessful response
        with patch('requests.request') as mock_req:
            mock_req.return_value.status_code = 200
            mock_req.return_value.json.return_value = {
                'IsSuccess': False,
                'Message': 'Payment not found',
            }
            with self.assertRaises(ValidationError):
                self.provider._myfatoorah_get_payment_status("12345")

        # Successful response
        with patch('requests.request') as mock_req:
            mock_req.return_value.status_code = 200
            mock_req.return_value.json.return_value = {
                'IsSuccess': True,
                'Data': {
                    'InvoiceStatus': 'Paid',
                    'InvoiceValue': 50.0,
                    'CustomerReference': 'TX-TEST-001',
                },
            }
            res = self.provider._myfatoorah_get_payment_status("12345")
            self.assertEqual(res['InvoiceStatus'], 'Paid')
            self.assertEqual(res['CustomerReference'], 'TX-TEST-001')

    def test_03_transaction_send_payment(self):
        """Test transaction send_payment process and error validations."""
        # Missing phone
        partner_no_phone = self.env['res.partner'].create({
            'name': 'No Phone Partner',
            'country_id': self.country_belgium.id,
            'phone': False,
        })
        tx_no_phone = self._create_transaction(
            flow='redirect', partner_id=partner_no_phone.id, reference='TX_NO_PHONE',
        )
        with self.assertRaises(ValueError):
            tx_no_phone.send_payment()

        # Invalid phone format
        partner_bad_phone = self.env['res.partner'].create({
            'name': 'Bad Phone Partner',
            'country_id': self.country_belgium.id,
            'phone': '+32',
        })
        tx_bad_phone = self._create_transaction(
            flow='redirect', partner_id=partner_bad_phone.id, reference='TX_BAD_PHONE',
        )
        with self.assertRaises(ValueError):
            tx_bad_phone.send_payment()

        tx = self._create_transaction(flow='redirect', reference='TX_VALID_SEND')

        # Successful payment request
        with patch('requests.request') as mock_req:
            mock_req.return_value.json.return_value = {
                'IsSuccess': True,
                'Data': {'InvoiceURL': 'https://myfatoorah.com/pay/invoice123'},
            }
            res = tx.send_payment()
            self.assertIn('api_url', res)
            self.assertEqual(res['data']['InvoiceURL'], 'https://myfatoorah.com/pay/invoice123')

        # Unsuccessful payment request with validation errors
        with patch('requests.request') as mock_req:
            mock_req.return_value.json.return_value = {
                'IsSuccess': False,
                'ValidationErrors': [{'Error': 'Invalid mobile number'}],
            }
            with self.assertRaises(ValidationError):
                tx.send_payment()

        # Test _get_specific_rendering_values
        with patch.object(type(tx), 'send_payment', return_value={'data': 'test_data'}) as mock_send:
            res = tx._get_specific_rendering_values({})
            self.assertEqual(res, {'data': 'test_data'})
            mock_send.assert_called_once()

    def test_04_extract_reference(self):
        """Test extraction of transaction reference."""
        tx_model = self.env['payment.transaction']
        ref1 = tx_model._extract_reference('myfatoorah', {'CustomerReference': 'REF_1001'})
        self.assertEqual(ref1, 'REF_1001')
        ref2 = tx_model._extract_reference('myfatoorah', {'reference': 'REF_1002'})
        self.assertEqual(ref2, 'REF_1002')

    def test_05_validate_amount(self):
        """Test amount validation behavior for MyFatoorah."""
        tx = self._create_transaction(flow='redirect', reference='TX_VAL_AMT')

        # Validation operation
        tx.with_context(payment_safe_write=True).operation = 'validation'
        self.assertIsNone(tx._validate_amount({'InvoiceValue': 100.0}))

        # Online redirect operation
        tx.with_context(payment_safe_write=True).operation = 'online_redirect'
        res = tx._validate_amount({
            'InvoiceValue': 15.5,
            'InvoiceStatus': 'Paid',
            'InvoiceTransactions': [{
                'PaidCurrency': 'KWD',
                'PaidCurrencyValue': 15.5,
            }],
        })
        self.assertIsNone(res)

    def test_06_apply_updates(self):
        """Test transaction status updates for all InvoiceStatus values."""
        # Paid
        tx1 = self._create_transaction(flow='redirect', reference='TX_PAID')
        tx1.with_context(payment_safe_write=True)._apply_updates({
            'InvoiceStatus': 'Paid',
            'InvoiceTransactions': [{'PaymentId': 'PAY_9999'}],
        })
        self.assertEqual(tx1.state, 'done')
        self.assertEqual(tx1.provider_reference, 'PAY_9999')

        # Pending
        tx2 = self._create_transaction(flow='redirect', reference='TX_PENDING')
        tx2.with_context(payment_safe_write=True)._apply_updates({
            'InvoiceStatus': 'Pending',
            'InvoiceTransactions': [{'TransactionId': 'TRX_8888'}],
        })
        self.assertEqual(tx2.state, 'pending')
        self.assertEqual(tx2.provider_reference, 'TRX_8888')

        # Failed
        tx3 = self._create_transaction(flow='redirect', reference='TX_FAILED')
        tx3.with_context(payment_safe_write=True)._apply_updates({
            'InvoiceStatus': 'Failed',
            'InvoiceId': 'INV_7777',
        })
        self.assertEqual(tx3.state, 'error')
        self.assertEqual(tx3.provider_reference, 'INV_7777')

        # Expired
        tx4 = self._create_transaction(flow='redirect', reference='TX_EXPIRED')
        tx4.with_context(payment_safe_write=True)._apply_updates({'InvoiceStatus': 'Expired'})
        self.assertEqual(tx4.state, 'error')

        # Canceled
        tx5 = self._create_transaction(flow='redirect', reference='TX_CANCELED')
        tx5.with_context(payment_safe_write=True)._apply_updates({'InvoiceStatus': 'Canceled'})
        self.assertEqual(tx5.state, 'error')

        # Invalid status
        tx6 = self._create_transaction(flow='redirect', reference='TX_INVALID')
        tx6.with_context(payment_safe_write=True)._apply_updates({'InvoiceStatus': 'Unrecognized'})
        self.assertEqual(tx6.state, 'error')

    def test_07_controllers(self):
        """Test controller routes."""
        self._disable_process_patcher()
        controller = PaymentMyFatoorahController()
        tx = self._create_transaction(flow='redirect', reference='TX_CTRL')

        # Test myfatoorah_payment_response
        test_data = repr({
            'CustomerName': 'Norbert Buyer',
            'DisplayCurrencyIso': 'USD',
            'CustomerMobile': '470123456',
            'InvoiceValue': 50.0,
            'CustomerAddress': {'Address': 'Huge Street, Sin City'},
            'InvoiceURL': 'https://myfatoorah.com/pay/123',
        })
        with mock_request(self.env):
            res = controller.myfatoorah_payment_response(data=test_data)
            self.assertEqual(res.status_code, 200)

        # Test myfatoorah_checkout with valid return
        return_payload = {
            'CustomerReference': tx.reference,
            'InvoiceStatus': 'Paid',
            'InvoiceTransactions': [{'PaymentId': 'P_12345'}],
        }
        with mock_request(self.env):
            with patch.object(type(self.provider), '_myfatoorah_get_payment_status', return_value=return_payload):
                res = controller.myfatoorah_checkout(paymentId='P_12345')
                self.assertIn(res.status_code, (200, 302, 303))
                self._run_processing()
                self.assertEqual(tx.state, 'done')

        # Test payment_failed
        with mock_request(self.env):
            res = controller.payment_failed()
            self.assertEqual(res.status_code, 200)
