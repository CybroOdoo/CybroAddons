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
from unittest.mock import patch

from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.payment.tests.http_common import PaymentHttpCommon
from odoo.addons.payment_paytabs_odoo.controllers.payment_paytabs_odoo import PaymentPaytabs
from odoo.addons.payment_paytabs_odoo.tests.common import PaytabsCommon


@tagged('post_install', '-at_install')
class TestProcessingFlows(PaytabsCommon, PaymentHttpCommon):

    @mute_logger('odoo.addons.payment_paytabs_odoo.controllers.payment_paytabs_odoo')
    def test_paytabs_return_get_triggers_processing(self):
        """ Test that a GET return request triggers transaction processing and redirects. """
        tx = self._create_transaction(flow='redirect')
        url = self._build_url(PaymentPaytabs._return_url)
        with patch(
            'odoo.addons.payment.models.payment_transaction.PaymentTransaction._process'
        ) as process_mock:
            response = self._make_http_get_request(url, params=self.return_data_authorized)
            self.assertEqual(process_mock.call_count, 1)
            self.assertEqual(process_mock.call_args[0][0], 'paytabs')
            self.assertEqual(response.status_code, 200)

    @mute_logger('odoo.addons.payment_paytabs_odoo.controllers.payment_paytabs_odoo')
    def test_paytabs_return_post_form_triggers_processing(self):
        """ Test that a POST return request with form data triggers transaction processing. """
        tx = self._create_transaction(flow='redirect')
        url = self._build_url(PaymentPaytabs._return_url)
        with patch(
            'odoo.addons.payment.models.payment_transaction.PaymentTransaction._process'
        ) as process_mock:
            response = self._make_http_post_request(url, data=self.return_data_authorized)
            self.assertEqual(process_mock.call_count, 1)
            self.assertEqual(process_mock.call_args[0][0], 'paytabs')
            self.assertEqual(response.status_code, 200)

    @mute_logger('odoo.addons.payment_paytabs_odoo.controllers.payment_paytabs_odoo')
    def test_paytabs_return_post_json_triggers_processing(self):
        """ Test that a POST return request with JSON payload triggers transaction processing. """
        tx = self._create_transaction(flow='redirect')
        url = self._build_url(PaymentPaytabs._return_url)
        with patch(
            'odoo.addons.payment.models.payment_transaction.PaymentTransaction._process'
        ) as process_mock:
            response = self._make_json_request(url, data=self.return_data_authorized)
            self.assertEqual(process_mock.call_count, 1)
            self.assertEqual(process_mock.call_args[0][0], 'paytabs')
            self.assertEqual(response.status_code, 200)

    @mute_logger('odoo.addons.payment_paytabs_odoo.controllers.payment_paytabs_odoo')
    def test_paytabs_webhook_post_form_triggers_processing(self):
        """ Test that a POST webhook with form data triggers processing and returns OK. """
        tx = self._create_transaction(flow='redirect')
        url = self._build_url(PaymentPaytabs._webhook_url)
        with patch(
            'odoo.addons.payment.models.payment_transaction.PaymentTransaction._process'
        ) as process_mock:
            response = self._make_http_post_request(url, data=self.webhook_data_authorized)
            self.assertEqual(process_mock.call_count, 1)
            self.assertEqual(process_mock.call_args[0][0], 'paytabs')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.text, 'OK')
            self.assertIn('text/plain', response.headers.get('Content-Type', ''))

    @mute_logger('odoo.addons.payment_paytabs_odoo.controllers.payment_paytabs_odoo')
    def test_paytabs_webhook_post_json_triggers_processing(self):
        """ Test that a POST webhook with JSON payload triggers processing and returns OK. """
        tx = self._create_transaction(flow='redirect')
        url = self._build_url(PaymentPaytabs._webhook_url)
        with patch(
            'odoo.addons.payment.models.payment_transaction.PaymentTransaction._process'
        ) as process_mock:
            response = self._make_json_request(url, data=self.webhook_data_authorized)
            self.assertEqual(process_mock.call_count, 1)
            self.assertEqual(process_mock.call_args[0][0], 'paytabs')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.text, 'OK')

    @mute_logger('odoo.addons.payment_paytabs_odoo.controllers.payment_paytabs_odoo')
    def test_paytabs_return_empty_payload(self):
        """ Test that an empty return request redirects gracefully without processing. """
        url = self._build_url(PaymentPaytabs._return_url)
        with patch(
            'odoo.addons.payment.models.payment_transaction.PaymentTransaction._process'
        ) as process_mock:
            response = self._make_http_get_request(url, params={})
            self.assertEqual(process_mock.call_count, 0)
            self.assertEqual(response.status_code, 200)

    @mute_logger('odoo.addons.payment_paytabs_odoo.controllers.payment_paytabs_odoo')
    def test_paytabs_webhook_empty_payload(self):
        """ Test that an empty webhook request returns OK without processing. """
        url = self._build_url(PaymentPaytabs._webhook_url)
        with patch(
            'odoo.addons.payment.models.payment_transaction.PaymentTransaction._process'
        ) as process_mock:
            response = self._make_http_post_request(url, data={})
            self.assertEqual(process_mock.call_count, 0)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.text, 'OK')

