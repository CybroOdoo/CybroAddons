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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo.tests import tagged

from .common import TenderManagementHttpCommon


@tagged('post_install', '-at_install')
class TestWebsitePages(TenderManagementHttpCommon):
    """Render the website and portal pages through HTTP requests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tender = cls.create_tender(tender_state='bid_submission')
        cls.portal_user = cls.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Vendor One',
            'login': 'vendor_one_web',
            'password': 'vendor_one_web',
            'partner_id': cls.vendor_1.id,
            'group_ids': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })

    def test_public_pages(self):
        for url in ('/tender_management', '/vendor_register', f'/show_tender/{self.tender.id}'):
            response = self.url_open(url)
            self.assertEqual(response.status_code, 200, url)
        details = self.url_open(f'/show_tender/{self.tender.id}').text
        self.assertIn('Test Tender', details)
        self.assertIn('Log in to submit a bid', details)
        self.assertEqual(self.url_open('/show_tender/999999').status_code, 404)

    def test_tender_snippet_rpc(self):
        tenders = self.make_jsonrpc_request('/tender_management_snippet', {})
        self.assertEqual([tender['id'] for tender in tenders], [self.tender.id])

    def test_document_download(self):
        document = self.tender.tender_file_ids[:1]
        response = self.url_open(f'/download/file/{document.id}')
        self.assertEqual(response.content, b'tender-data')
        self.assertIn('spec.txt', response.headers['Content-Disposition'])

    def test_portal_pages_for_vendor(self):
        bid = self.create_bid(self.tender, self.vendor_1)
        bid.bidding_state = 'bid_close'
        self.tender.registered_vendors_ids = [(4, self.vendor_1.id)]
        self.authenticate('vendor_one_web', 'vendor_one_web')
        my_tenders = self.url_open('/my/tenders')
        self.assertEqual(my_tenders.status_code, 200)
        self.assertIn('Test Tender', my_tenders.text)
        details = self.url_open(f'/show_tender/{self.tender.id}').text
        self.assertIn('Request edit', details)

        bid.edit_request = True
        details = self.url_open(f'/show_tender/{self.tender.id}').text
        self.assertIn('waiting for approval', details)
        self.assertNotIn('Request edit', details)

        bid.edit_request = False
        self.tender.tender_state = 'bid_evaluation'
        details = self.url_open(f'/show_tender/{self.tender.id}').text
        self.assertNotIn('Request edit', details)
        self.assertIn('not open for bidding', details)

    def test_product_template_download_requires_login(self):
        url = f'/tender/{self.tender.id}/product_template'
        self.assertNotIn('spreadsheetml', self.url_open(url).headers.get('Content-Type', ''))
        self.authenticate('admin', 'admin')
        response = self.url_open(url)
        self.assertIn('spreadsheetml', response.headers['Content-Type'])
        self.assertTrue(response.content.startswith(b'PK'))

    def test_tender_page_shows_decimal_quantity(self):
        self.tender.tender_product_line_ids[:1].product_qty = 2.5
        details = self.url_open(f'/show_tender/{self.tender.id}').text
        self.assertIn('data-qty="2.5"', details)
        self.assertIn('2.50', details)
