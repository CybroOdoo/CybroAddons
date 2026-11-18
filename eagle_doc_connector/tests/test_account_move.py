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
import base64
import json
from unittest.mock import patch

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from ..models.eagle_api import EagleDocAPI
from .common import EagleDocCommon, FakeResponse, set_param

SAMPLE = {
    'general': {
        'CustomerName': {'value': 'Brand New Vendor GmbH'},
        'CustomerVAT': {'value': 'DE 999.888-777'},
        'CustomerStreet': 'Main 1',
        'CustomerCity': 'Berlin',
        'CustomerZip': '10115',
        'CustomerCountry': 'Germany',
        'InvoiceNumber': {'value': 'INV-42'},
        'PurchaseOrderNumber': 'PO-7',
        'InvoiceDate': '15.01.2026',
        'InvoiceDueDate': 'garbage-date',
        'Currency': 'EUR',
        'TotalPrice': {'value': '115,00'},
    },
    'productItems': [{
        'ProductName': {'value': 'Widget'},
        'ProductQuantity': {'value': '1'},
        'ProductUnitPrice': {'value': '100,00'},
        'TaxPercentage': {'value': '15'},
        'DiscountPerc': {'value': '0'},
    }],
    'taxes': [{'TaxPercentage': {'value': '15'}, 'TaxNetAmount': {'value': '100'}}],
    'bookkeeping': {'entries': [
        {'accountNumber': '4400', 'counterAccountNumber': '1600',
         'taxCode': '9', 'amount': '115'}]},
}


@tagged('post_install', '-at_install')
class TestAccountMoveHelpers(EagleDocCommon):
    """Pure helper methods."""

    def test_parse_helpers(self):
        """Parse helpers."""
        move = self.env['account.move']
        self.assertEqual(move._eagle_doc_clean_vat(' de-12.3 '), 'DE123')
        self.assertEqual(move._eagle_doc_clean_vat(False), '')
        self.assertEqual(move._eagle_doc_unwrap({'value': 5}), 5)
        self.assertEqual(move._eagle_doc_unwrap(5), 5)
        self.assertEqual(move._eagle_doc_safe_float('€ 1,5'), 1.5)
        self.assertEqual(move._eagle_doc_safe_float(None, default=9), 9)
        self.assertEqual(move._eagle_doc_safe_float('abc', default=2), 2)
        self.assertEqual(move._eagle_doc_safe_float('', default=3), 3)

    def test_parse_date(self):
        """Parse date."""
        parse = self.env['account.move']._eagle_doc_parse_date
        self.assertEqual(parse('2026-01-15'), '2026-01-15')
        self.assertEqual(parse('15.01.2026'), '2026-01-15')
        self.assertEqual(parse('Monday, 15.01.2026'), '2026-01-15')
        self.assertEqual(parse('January 15, 2026'), '2026-01-15')
        self.assertEqual(parse('20260115'), '2026-01-15')
        with self.assertRaises(ValueError):
            parse('')
        with self.assertRaises(ValueError):
            parse('not a date')

    def test_parse_tax_rate(self):
        """Parse tax rate."""
        move = self.env['account.move']
        self.assertIsNone(move._eagle_doc_parse_tax_rate(None))
        self.assertEqual(move._eagle_doc_parse_tax_rate('19 %'), 19.0)
        self.assertEqual(move._eagle_doc_parse_tax_rate('0,19'), 19.0)
        self.assertEqual(move._eagle_doc_parse_tax_rate('7'), 7.0)
        self.assertIsNone(move._eagle_doc_parse_tax_rate('abc'))

    def test_is_sale_move(self):
        """Is sale move."""
        self.assertTrue(self.make_move('out_invoice')._eagle_doc_is_sale_move())
        self.assertFalse(self.make_move('in_invoice')._eagle_doc_is_sale_move())

    def test_raw_extraction_helpers(self):
        """Raw extraction helpers."""
        move = self.make_move()
        self.assertEqual(move._eagle_doc_raw_general(), {})
        move.eagle_doc_raw_extraction = 'not json'
        self.assertEqual(move._eagle_doc_raw_general(), {})
        move.eagle_doc_raw_extraction = json.dumps(SAMPLE)
        self.assertIn('CustomerName', move._eagle_doc_raw_general())
        raw_value = self.env['account.move']._eagle_doc_raw_value
        self.assertEqual(raw_value({'a': {'value': 'x'}}, 'a'), 'x')
        self.assertEqual(raw_value({'a': 'y'}, 'a'), 'y')
        self.assertEqual(raw_value({}, 'a'), '')


@tagged('post_install', '-at_install')
class TestAccountMoveTaxesAndProducts(EagleDocCommon):
    """Tests for account move taxes and products."""

    def test_find_existing_tax(self):
        """Find existing tax."""
        move = self.make_move('in_invoice')
        rate = self.company_data['default_tax_purchase'].amount
        self.assertEqual(
            move._eagle_doc_find_tax(rate),
            self.company_data['default_tax_purchase'])
        self.assertFalse(move._eagle_doc_find_tax(None))

    def test_find_missing_tax_posts_message(self):
        """Find missing tax posts message."""
        move = self.make_move('in_invoice')
        self.company.is_eagle_doc_auto_create_tax = False
        self.assertFalse(move._eagle_doc_find_tax(33.3))
        self.assertTrue(move.message_ids)

    def test_auto_create_tax(self):
        """Auto create tax."""
        move = self.make_move('in_invoice')
        self.company.is_eagle_doc_auto_create_tax = True
        # No placeholder account configured: nothing is created.
        self.assertFalse(move._eagle_doc_find_tax(12.5))
        account = self.company_data['default_account_tax_purchase']
        self.company.eagle_doc_auto_tax_account_purchase_id = account
        tax = move._eagle_doc_find_tax(12.5)
        self.assertEqual(tax.amount, 12.5)
        self.assertEqual(tax.type_tax_use, 'purchase')
        # Existing group is reused the second time around.
        group = move._eagle_doc_get_or_create_tax_group(12.5)
        self.assertEqual(group, move._eagle_doc_get_or_create_tax_group(12.5))

    def test_auto_create_sale_tax(self):
        """Auto create sale tax."""
        move = self.make_move('out_invoice')
        self.company.is_eagle_doc_auto_create_tax = True
        self.company.eagle_doc_auto_tax_account_sale_id = (
            self.company_data['default_account_tax_sale'])
        self.assertEqual(move._eagle_doc_find_tax(8.25).type_tax_use, 'sale')

    def test_find_or_create_product(self):
        """Find or create product."""
        move = self.make_move()
        self.assertFalse(move._eagle_doc_find_or_create_product(''))
        self.company.is_eagle_doc_auto_create_product = False
        self.assertFalse(move._eagle_doc_find_or_create_product('Unknown thing'))
        self.company.is_eagle_doc_auto_create_product = True
        product = move._eagle_doc_find_or_create_product(
            'Brand new thing', product_code='BNT-1', unit_price=5)
        self.assertEqual(product.default_code, 'BNT-1')
        self.assertEqual(
            move._eagle_doc_find_or_create_product('x', product_code='BNT-1'),
            product)
        self.assertEqual(
            move._eagle_doc_find_or_create_product('BRAND NEW THING'), product)
        self.assertEqual(
            move._eagle_doc_get_auto_product_category(),
            move._eagle_doc_get_auto_product_category())

    def test_find_or_create_partner(self):
        """Find or create partner."""
        move = self.make_move()
        self.assertFalse(move._eagle_doc_find_or_create_partner('  '))
        existing = self.env['res.partner'].create({
            'name': 'Has VAT', 'vat': 'BE0123456789', 'supplier_rank': 1})
        self.assertEqual(
            move._eagle_doc_find_or_create_partner(
                'whatever', {'vat': 'be 0123.456.789'}), existing)
        self.assertEqual(
            move._eagle_doc_find_or_create_partner('has vat'), existing)
        self.company.is_eagle_doc_auto_create_partner = False
        self.assertFalse(move._eagle_doc_find_or_create_partner('Totally Unknown'))
        self.company.is_eagle_doc_auto_create_partner = True
        created = move._eagle_doc_find_or_create_partner('Totally Unknown', {
            'street': 'S', 'city': 'C', 'zip': 'Z',
            'country_code_or_name': 'Germany', 'state_name': 'Berlin',
            'vat': 'DE111',
        })
        self.assertEqual(created.supplier_rank, 1)
        self.assertEqual(created.country_id.code, 'DE')
        unknown_country = move._eagle_doc_find_or_create_partner(
            'Other Unknown', {'country_code_or_name': 'Atlantis'})
        self.assertFalse(unknown_country.country_id)
        sale_partner = self.make_move('out_invoice')._eagle_doc_find_or_create_partner('Sale Co')
        self.assertEqual(sale_partner.customer_rank, 1)


@tagged('post_install', '-at_install')
class TestAccountMoveExtraction(EagleDocCommon):
    """Tests for account move extraction."""

    def setUp(self):
        """Prepare the fixtures for each test."""
        super().setUp()
        self.company.is_eagle_doc_auto_create_partner = True
        self.company.is_eagle_doc_auto_create_product = False

    def _blank_move(self, move_type='in_invoice'):
        return self.env['account.move'].create({'move_type': move_type})

    def test_apply_full_extraction(self):
        """Apply full extraction."""
        move = self._blank_move()
        move._apply_eagle_doc_extraction(json.loads(json.dumps(SAMPLE)))
        self.assertEqual(move.ref, 'INV-42')
        self.assertEqual(move.invoice_origin, 'PO-7')
        self.assertEqual(str(move.invoice_date), '2026-01-15')
        self.assertEqual(move.partner_id.name, 'Brand New Vendor GmbH')
        self.assertEqual(len(move.invoice_line_ids), 1)
        self.assertTrue(move.eagle_doc_raw_extraction)

    def test_apply_extraction_sale_and_unknown_currency(self):
        """Apply extraction sale and unknown currency."""
        data = json.loads(json.dumps(SAMPLE))
        data['general']['Currency'] = 'ZZZ'
        data['general']['InvoiceDueDate'] = '2026-02-15'
        move = self._blank_move('out_invoice')
        move._apply_eagle_doc_extraction(data)
        self.assertEqual(move.ref, 'PO-7')
        self.assertEqual(str(move.invoice_date_due), '2026-02-15')

    def test_apply_extraction_relinks_attachment(self):
        """Apply extraction relinks attachment."""
        other = self.make_move()
        attachment = self.env['ir.attachment'].create({
            'name': 'a.pdf', 'raw': b'x',
            'res_model': 'account.move', 'res_id': other.id})
        move = self._blank_move()
        move._apply_eagle_doc_extraction(
            {'general': {}}, original_attachment=attachment)
        self.assertEqual(attachment.res_id, move.id)

    def test_apply_lines_tax_resolution(self):
        """Apply lines tax resolution."""
        move = self._blank_move()
        tax = self.company_data['default_tax_purchase']
        rate = tax.amount
        items = [
            {'ProductName': 'Explicit', 'ProductUnitPrice': '10',
             'TaxPercentage': str(rate)},
            {'ProductName': 'Single bracket', 'ProductUnitPrice': '10'},
            {'ProductName': 'Unmatched', 'ProductUnitPrice': '10',
             'TaxPercentage': '1.23'},
            {'ProductUnitPrice': '5'},
        ]
        move._eagle_doc_apply_lines(
            items, top_level_taxes=[
                {'TaxPercentage': str(rate), 'TaxNetAmount': '10'}])
        self.assertEqual(len(move.invoice_line_ids), 4)
        self.assertTrue(move.message_ids)

    def test_apply_lines_multiple_brackets(self):
        """Apply lines multiple brackets."""
        move = self._blank_move()
        rate = self.company_data['default_tax_purchase'].amount
        items = [
            {'ProductName': 'In bracket', 'ProductUnitPrice': '10', 'ProductQuantity': '2'},
            {'ProductName': 'No bracket', 'ProductUnitPrice': '77'},
        ]
        move._eagle_doc_apply_lines(items, top_level_taxes=[
            {'TaxPercentage': str(rate), 'TaxNetAmount': '20'},
            {'TaxPercentage': '99', 'TaxNetAmount': '500'},
        ])
        self.assertEqual(len(move.invoice_line_ids), 2)

    def test_apply_lines_empty(self):
        """Apply lines empty."""
        move = self._blank_move()
        self.assertIsNone(move._eagle_doc_apply_lines([]))

    def test_total_mismatch(self):
        """Total mismatch."""
        move = self.make_move()
        move._eagle_doc_check_total_mismatch('9999')
        self.assertTrue(move.is_eagle_doc_total_mismatch)
        move._eagle_doc_check_total_mismatch(str(move.amount_total))
        self.assertFalse(move.is_eagle_doc_total_mismatch)
        move._eagle_doc_check_total_mismatch(None)
        self.assertFalse(move.is_eagle_doc_total_mismatch)

    def test_action_post_rechecks_total(self):
        """Action post rechecks total."""
        move = self.make_move(
            eagle_doc_document_id='D1',
            eagle_doc_raw_extraction=json.dumps(
                {'general': {'TotalPrice': {'value': '9999'}}}))
        move.action_post()
        self.assertTrue(move.is_eagle_doc_total_mismatch)
        bad = self.make_move(
            eagle_doc_document_id='D2', eagle_doc_raw_extraction='{not json')
        bad.action_post()
        self.assertEqual(bad.state, 'posted')


@tagged('post_install', '-at_install')
class TestAccountMoveFeedback(EagleDocCommon):
    """Tests for account move feedback."""

    def setUp(self):
        """Prepare the fixtures for each test."""
        super().setUp()
        self.move = self.make_move(
            eagle_doc_sub_business_id='SB1',
            eagle_doc_raw_extraction=json.dumps({
                'general': {
                    'CustomerName': 'Old Name',
                    'BK_CustomerAccountNumber': '70000',
                    'CustomerCity': 'Old City',
                    'CustomerStreet': 'Old Street',
                    'BK_Account': '4000', 'BK_TaxKey': '8',
                },
                'productItems': [{
                    'ProductName': 'Old product',
                    'BK_Account': '4100', 'BK_TaxKey': '9'}],
            }))

    def test_vendor_feedback(self):
        """Vendor feedback."""
        with self.patch_http('post', FakeResponse(200, {'outcome': 'CREATED'})) as post:
            self.move.action_eagle_doc_submit_vendor_feedback(
                'New', '70001', new_vendor_city='C', new_vendor_street='S')
        payload = post.call_args.kwargs['json']
        self.assertEqual(payload['oldVendorName'], 'Old Name')
        self.assertEqual(payload['newVendorCity'], 'C')

    def test_product_feedback(self):
        """Product feedback."""
        with self.patch_http('post', FakeResponse(200, {'outcome': 'CREATED'})) as post:
            self.move.action_eagle_doc_submit_product_feedback('New', '4400')
        payload = post.call_args.kwargs['json']
        self.assertEqual(payload['productName'], 'Old product')
        self.assertEqual(payload['bkAccountNumber'], '4100')
        self.assertEqual(payload['docType'], 'INCOMING_INVOICE')

    def test_product_feedback_falls_back_to_general(self):
        """Product feedback falls back to general."""
        self.move.eagle_doc_raw_extraction = json.dumps(
            {'general': {'BK_Account': '4000', 'BK_TaxKey': '8'}})
        with self.patch_http('post', FakeResponse(200, {})) as post:
            self.move.action_eagle_doc_submit_product_feedback(
                'New', '4400', product_name='Given')
        payload = post.call_args.kwargs['json']
        self.assertEqual(payload['bkAccountNumber'], '4000')
        self.assertEqual(payload['taxCode'], '8')

    def test_feedback_requires_sub_business(self):
        """Feedback requires sub business."""
        self.move.eagle_doc_sub_business_id = False
        with self.assertRaises(UserError):
            self.move.action_eagle_doc_submit_vendor_feedback('a', 'b')
        with self.assertRaises(UserError):
            self.move.action_eagle_doc_submit_product_feedback('a', 'b')


@tagged('post_install', '-at_install')
class TestAccountMoveScan(EagleDocCommon):
    """Tests for account move scan."""

    @staticmethod
    def _stub_api():
        """Patch the EagleDocAPI methods used by the scan flow."""
        return [
            patch.object(EagleDocAPI, 'get_or_create_default_sub_business',
                         return_value='SB1'),
            patch.object(EagleDocAPI, 'upload_invoice',
                         return_value={'taskId': 'T1', 'status': 'PROCESSING'}),
        ]

    def _scan(self, filename='bill.pdf', move_type='in_invoice'):
        patches = self._stub_api()
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        return self.env['account.move'].action_scan_via_eagle_doc(
            filename, base64.b64encode(b'%PDF-1.4').decode(), move_type)

    def test_scan_queues_upload_for_cron(self):
        """Scan only uploads; the cron applies the result later."""
        with patch.object(EagleDocAPI, 'get_invoice_status') as poll:
            action = self._scan()
        poll.assert_not_called()
        move = self.env['account.move'].browse(action['res_id'])
        self.assertEqual(move.eagle_doc_status, 'processing')
        self.assertEqual(move.eagle_doc_task_id, 'T1')
        self.assertEqual(move.eagle_doc_sub_business_id, 'SB1')
        self.assertFalse(move.eagle_doc_document_id)

    def test_scan_outgoing_invoice(self):
        """Scan outgoing invoice."""
        action = self._scan(move_type='out_invoice')
        self.assertTrue(action['res_id'])

    def test_scan_upload_failure(self):
        """Scan upload failure."""
        patches = self._stub_api()
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        with patch.object(EagleDocAPI, 'upload_invoice',
                          side_effect=UserError('boom')):
            with self.assertRaises(UserError):
                self.env['account.move'].action_scan_via_eagle_doc(
                    'bill.pdf', 'aGVsbG8=')

    def test_scan_validation(self):
        """Scan validation."""
        move_model = self.env['account.move']
        with self.assertRaises(UserError):
            move_model.action_scan_via_eagle_doc('bill.exe', 'aGVsbG8=')
        set_param(self.env, 'eagle_doc.api_key', '')
        with self.assertRaises(UserError):
            move_model.action_scan_via_eagle_doc('bill.pdf', 'aGVsbG8=')

    def test_scan_requires_accounting_group(self):
        """Scan requires accounting group."""
        user = self.env['res.users'].create({
            'name': 'Nobody', 'login': 'nobody_eagle',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        with self.assertRaises(AccessError):
            self.env['account.move'].with_user(user).action_scan_via_eagle_doc(
                'bill.pdf', 'aGVsbG8=')


@tagged('post_install', '-at_install')
class TestAccountMoveCron(EagleDocCommon):
    """Tests for account move cron."""

    def setUp(self):
        """Prepare the fixtures for each test."""
        super().setUp()
        self.moves = self.make_move(), self.make_move()
        self.moves[0].write({
            'eagle_doc_task_id': 'T1', 'eagle_doc_sub_business_id': 'SB1',
            'eagle_doc_status': 'processing'})
        self.moves[1].write({
            'eagle_doc_task_id': 'T2', 'eagle_doc_sub_business_id': 'SB1',
            'eagle_doc_status': 'processing'})

    def test_cron_without_pending_moves(self):
        """Cron without pending moves."""
        self.moves[0].eagle_doc_status = 'processed'
        self.moves[1].eagle_doc_status = 'processed'
        self.assertIsNone(
            self.env['account.move']._cron_process_eagle_doc_uploads())

    def test_cron_applies_results(self):
        """Cron applies results."""
        batch = {
            'results': [
                {'taskId': 'T1', 'status': 'PROCESSED', 'documentId': 'D1'},
                {'taskId': 'T2', 'status': 'FAILED'},
                {'taskId': 'UNKNOWN', 'status': 'PROCESSED'},
            ],
            'notFound': ['T9'],
        }
        with patch.object(EagleDocAPI, 'get_invoice_statuses_batch',
                          return_value=batch), \
                patch.object(EagleDocAPI, 'get_processed_document',
                             return_value={'general': {}}):
            self.env['account.move']._cron_process_eagle_doc_uploads()
        self.assertEqual(self.moves[0].eagle_doc_status, 'processed')
        self.assertEqual(self.moves[1].eagle_doc_status, 'failed')

    def test_cron_isolates_failures_with_savepoint(self):
        """Cron isolates failures with savepoint."""
        batch = {'results': [
            {'taskId': 'T1', 'status': 'PROCESSED', 'documentId': 'D1'},
            {'taskId': 'T2', 'status': 'FAILED'},
        ]}
        with patch.object(EagleDocAPI, 'get_invoice_statuses_batch',
                          return_value=batch), \
                patch.object(EagleDocAPI, 'get_processed_document',
                             side_effect=UserError('fetch failed')):
            self.env['account.move']._cron_process_eagle_doc_uploads()
        # First move's partial write was rolled back; second move still done.
        self.assertEqual(self.moves[0].eagle_doc_status, 'processing')
        self.assertEqual(self.moves[1].eagle_doc_status, 'failed')

    def test_cron_survives_batch_call_failure(self):
        """Cron survives batch call failure."""
        with patch.object(EagleDocAPI, 'get_invoice_statuses_batch',
                          side_effect=UserError('down')):
            self.env['account.move']._cron_process_eagle_doc_uploads()
        self.assertEqual(self.moves[0].eagle_doc_status, 'processing')
