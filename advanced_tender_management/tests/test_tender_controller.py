# -*- coding: utf-8 -*-
import ast
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

from odoo.addons.advanced_tender_management.controllers.tender import Tender

from .common import TenderManagementTestCommon


class _UploadedFile:
    def __init__(self, name, payload):
        self.filename = name
        self._payload = payload

    def read(self):
        return self._payload


class TestTenderController(TenderManagementTestCommon):
    """Tests for tender website controller."""

    def setUp(self):
        super().setUp()
        self.tender = self.create_tender(tender_state='bid_submission')
        self.portal_user = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Portal Vendor',
            'login': 'portal_vendor@example.com',
            'partner_id': self.vendor_1.id,
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
        })

    def _request(self, user=None):
        user = user or self.portal_user
        rendered = {}
        req = SimpleNamespace(
            env=self.env(user=user.id),
            user=user,
            render=lambda template, values=None: rendered.update({
                'template': template,
                'values': values or {},
            }) or rendered,
        )
        req.env.user = user
        req.rendered = rendered
        return req

    def test_edit_request_marks_bid_and_sends_mail(self):
        bid = self.create_bid(self.tender, self.vendor_1)
        controller = Tender()
        req = self._request()

        with patch('odoo.addons.mail.models.mail_template.MailTemplate.send_mail') as send_mail, \
                patch('odoo.addons.advanced_tender_management.controllers.tender.request', req):
            controller.edit_request(bid_id=str(bid.id))

        self.assertTrue(bid.edit_request)
        self.assertEqual(send_mail.call_count, 1)

    def test_submit_bit_creates_and_updates_bid(self):
        controller = Tender()
        req = self._request()
        payload = str([
            (self.product_1.id, 10),
            (self.product_2.id, 20),
        ])

        with patch('odoo.addons.mail.models.mail_template.MailTemplate.send_mail'), \
                patch('odoo.addons.advanced_tender_management.controllers.tender.request', req):
            result = controller.submit_bit(
                tender_id=str(self.tender.id),
                product_bid_list=payload,
                att=_UploadedFile('bid.txt', b'bid-file'),
            )
            existing_bid = self.env['tender.bidding'].search([
                ('tender_id', '=', self.tender.id),
                ('vendor_id', '=', self.vendor_1.id),
            ], limit=1)
            controller.submit_bit(
                tender_id=str(self.tender.id),
                product_bid_list=str([(self.product_1.id, 30), (self.product_2.id, 40)]),
            )

        self.assertEqual(result['template'], 'advanced_tender_management.bid_submitted_thankyou_page')
        self.assertEqual(existing_bid.bidding_state, 'bid_close')
        self.assertEqual(existing_bid.qualification_stage, 'initial')
        self.assertIn(self.vendor_1, self.tender.registered_vendors_ids)

    def test_get_tenders_and_render_pages(self):
        controller = Tender()
        req = self._request()

        with patch('odoo.addons.advanced_tender_management.controllers.tender.request', req):
            tenders = controller.get_tenders()
            success_page = controller.render_edit_request_success_page()
            detail_page = controller.render_tender_details(self.tender.id)
            snippet_page = controller.render_tender_template()

        self.assertEqual(len(tenders), 1)
        self.assertEqual(tenders[0]['tender_type'], 'Single vendor')
        self.assertEqual(success_page['template'], 'advanced_tender_management.edit_request_submitted_page')
        self.assertEqual(detail_page['template'], 'advanced_tender_management.tender_details')
        self.assertEqual(snippet_page['template'], 'advanced_tender_management.tender_snippet_template')
