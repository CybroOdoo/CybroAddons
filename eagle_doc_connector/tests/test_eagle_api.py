# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from unittest.mock import MagicMock

import requests
from odoo.exceptions import UserError
from odoo.tests import tagged

from ..models.eagle_api import EagleDocAPI
from .common import EagleDocCommon, FakeResponse, set_param


@tagged('post_install', '-at_install')
class TestEagleDocAPI(EagleDocCommon):
    """Tests for the Eagle Doc API client."""

    def setUp(self):
        """Prepare the fixtures for each test."""
        super().setUp()
        self.api = EagleDocAPI(self.env)
        self.attachment = self.env['ir.attachment'].create({
            'name': 'invoice.pdf',
            'raw': b'%PDF-1.4 test',
            'mimetype': 'application/pdf',
        })

    # -- helpers ----------------------------------------------------------
    def _calls(self):
        """(verb, method name, args, success payload, status -> expected)."""
        att = self.attachment
        return [
            ('post', 'upload_invoice', ('SB1', att), {'taskId': 'T1'}),
            ('get', 'get_invoice_status', ('SB1', 'T1'), {'status': 'PROCESSED'}),
            ('get', 'get_invoice_statuses_batch', ('SB1', ['T1']), {'results': []}),
            ('get', 'get_processed_document', ('SB1', 'D1'), {'general': {}}),
            ('get', 'list_sub_businesses', (), {'content': []}),
            ('get', 'get_sub_business', ('SB1',), {'id': 'SB1'}),
            ('post', 'create_sub_business', ({'businessName': 'X'},), {'id': 'SB1'}),
            ('post', 'batch_create_sub_businesses', ([{'businessName': 'X'}],), {'results': []}),
            ('patch', 'update_sub_business', ('SB1', {'businessName': 'Y'}), {'id': 'SB1'}),
            ('post', 'sync_vendor_customers_batch', ('SB1', [{'accountNumber': '1'}]), {'created': 1}),
            ('post', 'submit_vendor_feedback', ('SB1', {'a': 1}), {'outcome': 'CREATED'}),
            ('post', 'submit_product_feedback', ('SB1', {'a': 1}), {'outcome': 'CREATED'}),
            ('get', 'get_usage', ('2026-01',), {'totals': {}}),
        ]

    # -- basics -----------------------------------------------------------
    def test_init_reads_parameters(self):
        """Init reads parameters."""
        self.assertEqual(self.api.api_key, 'test-key')
        self.assertEqual(self.api.base_url, 'https://eagle.test')

    def test_default_base_url(self):
        """Default base url."""
        set_param(self.env, 'eagle_doc.base_url', '')
        api = EagleDocAPI(self.env)
        self.assertIn('eagle-doc.com', api.base_url)

    def test_headers(self):
        """Headers."""
        headers = self.api._get_headers('idem')
        self.assertEqual(headers['X-Partner-Api-Key'], 'test-key')
        self.assertEqual(headers['Idempotency-Key'], 'idem')
        self.assertNotIn('Idempotency-Key', self.api._get_headers())

    def test_headers_without_key(self):
        """Headers without key."""
        self.api.api_key = False
        with self.assertRaises(UserError):
            self.api._get_headers()

    def test_extract_error_message(self):
        """Extract error message."""
        error = requests.exceptions.HTTPError(
            response=FakeResponse(400, {'code': 'E1', 'message': 'bad'}))
        self.assertEqual(self.api._extract_error_message(error), 'E1: bad')
        error = requests.exceptions.HTTPError(
            response=FakeResponse(500, ValueError('no json'), text='plain'))
        self.assertEqual(self.api._extract_error_message(error), 'plain')
        error = requests.exceptions.HTTPError('boom')
        error.response = None
        self.assertEqual(self.api._extract_error_message(error), 'boom')

    # -- generic success / failure for every endpoint -------------------------
    def test_success_for_each_endpoint(self):
        """Success for each endpoint."""
        for verb, name, args, payload in self._calls():
            with self.subTest(method=name), self.patch_http(
                    verb, FakeResponse(200, payload)):
                self.assertEqual(getattr(self.api, name)(*args), payload)

    def test_server_error_for_each_endpoint(self):
        """Server error for each endpoint."""
        for verb, name, args, _payload in self._calls():
            with self.subTest(method=name), self.patch_http(
                    verb, FakeResponse(500, {'code': 'X', 'message': 'down'})):
                with self.assertRaises(UserError):
                    getattr(self.api, name)(*args)

    def test_connection_error_for_each_endpoint(self):
        """Connection error for each endpoint."""
        for verb, name, args, _payload in self._calls():
            with self.subTest(method=name), self.patch_http(
                    verb, side_effect=requests.exceptions.ConnectionError('net')):
                with self.assertRaises(UserError):
                    getattr(self.api, name)(*args)

    def test_specific_status_codes(self):
        """Specific status codes."""
        cases = [
            ('post', 'upload_invoice', ('SB1', self.attachment), (404, 400, 409)),
            ('get', 'get_invoice_status', ('SB1', 'T1'), (404,)),
            ('get', 'get_invoice_statuses_batch', ('SB1', ['T1']), (400,)),
            ('get', 'get_processed_document', ('SB1', 'D1'), (404,)),
            ('get', 'get_sub_business', ('SB1',), (404,)),
            ('post', 'create_sub_business', ({},), (403,)),
            ('post', 'batch_create_sub_businesses', ([{'a': 1}],), (400,)),
            ('delete', 'delete_sub_business', ('SB1',), (404,)),
            ('patch', 'update_sub_business', ('SB1', {}), (404,)),
            ('post', 'sync_vendor_customers_batch', ('SB1', [{'a': 1}]), (404, 400)),
            ('post', 'submit_vendor_feedback', ('SB1', {}), (404, 400)),
            ('post', 'submit_product_feedback', ('SB1', {}), (404, 400)),
            ('get', 'get_usage', ('bad',), (400,)),
        ]
        for verb, name, args, codes in cases:
            for code in codes:
                with self.subTest(method=name, code=code), self.patch_http(
                        verb, FakeResponse(code, {'code': 'C', 'message': 'm'})):
                    with self.assertRaises(UserError):
                        getattr(self.api, name)(*args)

    # -- individual behaviours ----------------------------------------------
    def test_upload_requires_sub_business(self):
        """Upload requires sub business."""
        with self.assertRaises(UserError):
            self.api.upload_invoice(False, self.attachment)

    def test_upload_with_raw_and_empty_attachment(self):
        """Upload sends the raw bytes, or an empty body without content."""
        fake = MagicMock(raw=b'hello', mimetype='text/plain')
        fake.name = 'a.pdf'
        with self.patch_http('post', FakeResponse(200, {'ok': 1})) as post:
            self.api.upload_invoice('SB1', fake, idempotency_key='k')
            self.assertEqual(
                post.call_args.kwargs['files']['file'][1], b'hello')
        fake = MagicMock(raw=False, mimetype='text/plain')
        fake.name = 'a.pdf'
        with self.patch_http('post', FakeResponse(200, {'ok': 1})) as post:
            self.api.upload_invoice('SB1', fake)
            self.assertEqual(post.call_args.kwargs['files']['file'][1], b'')

    def test_batch_status_validation(self):
        """Batch status validation."""
        with self.assertRaises(UserError):
            self.api.get_invoice_statuses_batch('SB1', [])
        with self.assertRaises(UserError):
            self.api.get_invoice_statuses_batch('SB1', ['t'] * 201)

    def test_batch_create_validation(self):
        """Batch create validation."""
        with self.assertRaises(UserError):
            self.api.batch_create_sub_businesses([])
        with self.assertRaises(UserError):
            self.api.batch_create_sub_businesses([{}] * 201)

    def test_sync_validation(self):
        """Sync validation."""
        with self.assertRaises(UserError):
            self.api.sync_vendor_customers_batch(False, [{'a': 1}])
        with self.assertRaises(UserError):
            self.api.sync_vendor_customers_batch('SB1', [])
        with self.assertRaises(UserError):
            self.api.sync_vendor_customers_batch('SB1', [{}] * 501)

    def test_feedback_requires_sub_business(self):
        """Feedback requires sub business."""
        with self.assertRaises(UserError):
            self.api.submit_vendor_feedback(False, {})
        with self.assertRaises(UserError):
            self.api.submit_product_feedback(False, {})

    def test_list_sub_businesses_with_query(self):
        """List sub businesses with query."""
        with self.patch_http('get', FakeResponse(200, {'content': []})) as get:
            self.api.list_sub_businesses(query='acme')
            self.assertEqual(get.call_args.kwargs['params']['q'], 'acme')

    def test_get_usage_without_period(self):
        """Get usage without period."""
        with self.patch_http('get', FakeResponse(200, {'totals': {}})) as get:
            self.api.get_usage()
            self.assertEqual(get.call_args.kwargs['params'], {})

    def test_delete_success(self):
        """Delete success."""
        with self.patch_http('delete', FakeResponse(204)):
            self.assertTrue(self.api.delete_sub_business('SB1'))

    # -- default sub-business -------------------------------------------------
    def test_default_sub_business_reuses_existing(self):
        """Default sub business reuses existing."""
        self.company.eagle_sub_business_id = 'EXISTING'
        with self.patch_http('post') as post:
            self.assertEqual(
                self.api.get_or_create_default_sub_business(), 'EXISTING')
            post.assert_not_called()

    def test_default_sub_business_created(self):
        """Default sub business created."""
        self.company.eagle_sub_business_id = False
        with self.patch_http('post', FakeResponse(200, {'id': 'NEW'})):
            self.assertEqual(
                self.api.get_or_create_default_sub_business(), 'NEW')
        self.assertEqual(self.company.eagle_sub_business_id, 'NEW')

    def test_default_sub_business_failures(self):
        """Default sub business failures."""
        self.company.eagle_sub_business_id = False
        with self.patch_http('post', FakeResponse(200, {})):
            with self.assertRaises(UserError):
                self.api.get_or_create_default_sub_business()
        with self.patch_http('post', FakeResponse(403)):
            with self.assertRaises(UserError):
                self.api.get_or_create_default_sub_business()
        with self.patch_http('post', FakeResponse(500, {'message': 'x'})):
            with self.assertRaises(UserError):
                self.api.get_or_create_default_sub_business()
        with self.patch_http(
                'post', side_effect=requests.exceptions.Timeout('slow')):
            with self.assertRaises(UserError):
                self.api.get_or_create_default_sub_business()
