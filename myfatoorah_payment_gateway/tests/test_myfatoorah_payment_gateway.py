# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Harshitha AP (odoo@cybrosys.com)
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
from unittest.mock import Mock, patch

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestMyFatoorah(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.provider = cls.env.ref(
            "myfatoorah_payment_gateway.payment_provider_myfatoorah"
        )

        cls.provider.write({
            "state": "test",
            "myfatoorah_token": "dummy_token",
        })

    # ------------------------------------------------------------------
    # Provider
    # ------------------------------------------------------------------

    def test_api_url_test(self):
        self.provider.state = "test"

        self.assertEqual(
            self.provider._myfatoorah_get_api_url(),
            "https://apitest.myfatoorah.com/",
        )

    def test_api_url_enabled(self):
        self.provider.state = "enabled"

        self.assertEqual(
            self.provider._myfatoorah_get_api_url(),
            "https://api.myfatoorah.com/",
        )

    # ------------------------------------------------------------------
    # send_payment()
    # ------------------------------------------------------------------

    def test_send_payment_without_phone(self):
        """send_payment should fail if partner phone is missing."""

        tx = self.env["payment.transaction"].new({
            "provider_id": self.provider.id,
            "provider_code": "myfatoorah",
            "partner_phone": False,
        })

        with self.assertRaises(ValueError):
            tx.send_payment()

    @patch(
        "odoo.addons.myfatoorah_payment_gateway.models.payment_transaction.requests.request"
    )
    def test_send_payment_api_failure(self, mock_request):
        """API should raise ValidationError when IsSuccess=False."""

        response = Mock()

        response.json.return_value = {
            "IsSuccess": False,
            "ValidationErrors": [
                {
                    "Name": "CustomerMobile",
                    "Error": "Invalid mobile",
                }
            ],
        }

        mock_request.return_value = response

        tx = self.env["payment.transaction"].new({
            "provider_id": self.provider.id,
            "provider_code": "myfatoorah",
            "partner_phone": "919876543210",
            "partner_name": "Test",
            "partner_email": "a@a.com",
            "amount": 100,
            "reference": "TEST001",
        })

        with self.assertRaises(Exception):
            tx.send_payment()