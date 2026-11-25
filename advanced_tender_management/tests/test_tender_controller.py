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
import io
import json
from types import SimpleNamespace
from unittest.mock import patch

from werkzeug.exceptions import NotFound

from odoo.tests import tagged

from odoo.addons.advanced_tender_management.controllers.tender import Tender

from .common import TenderManagementTestCommon


class _UploadedFile(io.BytesIO):
    def __init__(self, name, payload):
        super().__init__(payload)
        self.filename = name


@tagged('post_install', '-at_install')
class TestTenderController(TenderManagementTestCommon):
    """Tests for tender website controller."""

    def setUp(self):
        super().setUp()
        self.tender = self.create_tender(tender_state='bid_submission')
        self.portal_user = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Portal Vendor',
            'login': 'portal_vendor@example.com',
            'partner_id': self.vendor_1.id,
            'group_ids': [(6, 0, [self.env.ref('base.group_portal').id])],
        })

    def _request(self, user=None):
        user = user or self.portal_user
        return SimpleNamespace(
            env=self.env(user=user.id),
            render=lambda template, values=None: {'template': template, 'values': values or {}},
            redirect=lambda url: ('redirect', url),
        )

    def _submit(self, req, prices, **extra):
        with patch('odoo.addons.mail.models.mail_template.MailTemplate.send_mail'), \
                patch('odoo.addons.advanced_tender_management.controllers.tender.request', req):
            return self.call_route(Tender().submit_bit, 
                tender_id=str(self.tender.id),
                product_bid_list=json.dumps([[self.product_1.id, prices[0]],
                                             [self.product_2.id, prices[1]]]),
                **extra)

    def _bid(self):
        return self.env['tender.bidding'].search([
            ('tender_id', '=', self.tender.id), ('vendor_id', '=', self.vendor_1.id)])

    def test_edit_request_marks_bid_and_sends_mail(self):
        bid = self.create_bid(self.tender, self.vendor_1)
        bid.bidding_state = 'bid_close'

        with patch('odoo.addons.mail.models.mail_template.MailTemplate.send_mail') as send_mail, \
                patch('odoo.addons.advanced_tender_management.controllers.tender.request',
                      self._request()):
            result = Tender().edit_request(bid_id=str(bid.id))

        self.assertTrue(result['success'])
        self.assertTrue(bid.edit_request)
        self.assertEqual(send_mail.call_count, 1)

    def test_edit_request_on_another_vendors_bid_is_refused(self):
        bid = self.create_bid(self.tender, self.vendor_2)
        bid.bidding_state = 'bid_close'

        with patch('odoo.addons.advanced_tender_management.controllers.tender.request',
                   self._request()):
            result = Tender().edit_request(bid_id=str(bid.id))

        self.assertFalse(result['success'])
        self.assertFalse(bid.edit_request)

    def test_edit_request_after_bidding_closed_is_refused(self):
        bid = self.create_bid(self.tender, self.vendor_1)
        bid.bidding_state = 'bid_close'
        self.tender.tender_state = 'bid_evaluation'

        with patch('odoo.addons.advanced_tender_management.controllers.tender.request',
                   self._request()):
            result = Tender().edit_request(bid_id=str(bid.id))

        self.assertFalse(result['success'])
        self.assertFalse(bid.edit_request)

    def test_submit_bid_creates_bid_with_decimal_prices(self):
        result = self._submit(self._request(), (10.5, 20),
                              att=_UploadedFile('bid.pdf', b'bid-file'))

        bid = self._bid()
        self.assertEqual(result['template'], 'advanced_tender_management.bid_submitted_thankyou_page')
        self.assertEqual(bid.bidding_state, 'bid_close')
        self.assertEqual(bid.qualification_stage, 'initial')
        self.assertEqual(bid.total_bidding_amount, 10.5 * 3 + 20 * 2)
        self.assertEqual(bid.vendor_attachments_ids.name, 'bid.pdf')
        self.assertIn(self.vendor_1, self.tender.registered_vendors_ids)

    def test_submitted_bid_can_only_change_after_approved_edit(self):
        self._submit(self._request(), (10, 20))
        bid = self._bid()

        result = self._submit(self._request(), (1, 1))
        self.assertEqual(result, ('redirect', f'/show_tender/{self.tender.id}'))
        self.assertEqual(bid.total_bidding_amount, 70)

        bid.bidding_state = 'bid'
        self._submit(self._request(), (30, 40))
        self.assertEqual(bid.total_bidding_amount, 170)
        self.assertEqual(bid.bidding_state, 'bid_close')
        self.assertEqual(len(self._bid()), 1)

    def test_submit_bid_on_closed_tender_is_not_found(self):
        self.tender.tender_state = 'bid_evaluation'
        with self.assertRaises(NotFound):
            self._submit(self._request(), (10, 20))
        self.assertFalse(self._bid())

    def test_get_tenders_and_render_pages(self):
        other_category = self.env['tender.category'].create({'name': 'Other'})
        self.create_tender(name='Hidden', tender_state='bid_submission',
                           tender_category_id=other_category.id)
        bid = self.create_bid(self.tender, self.vendor_1)
        self.tender.registered_vendors_ids = [(4, self.vendor_1.id)]

        with patch('odoo.addons.advanced_tender_management.controllers.tender.request',
                   self._request()):
            tenders = Tender().get_tenders()
            success_page = self.call_route(Tender().render_edit_request_success_page)
            detail_page = self.call_route(Tender().render_tender_details, self.tender.id)
            with self.assertRaises(NotFound):
                self.call_route(Tender().render_tender_details, 999999)
            snippet_page = self.call_route(Tender().render_tender_template)

        self.assertEqual([tender['name'] for tender in tenders], ['Test Tender'])
        self.assertEqual(tenders[0]['tender_type'], 'Single vendor')
        self.assertEqual(success_page['template'], 'advanced_tender_management.edit_request_submitted_page')
        self.assertEqual(detail_page['template'], 'advanced_tender_management.tender_details')
        self.assertTrue(detail_page['values']['has_registered'])
        self.assertEqual(detail_page['values']['bid_record'], bid)
        self.assertEqual(snippet_page['template'], 'advanced_tender_management.tender_snippet_template')
