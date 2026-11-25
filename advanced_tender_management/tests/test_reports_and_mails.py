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
from unittest.mock import patch

from odoo.tests import tagged

from .common import TenderManagementTestCommon


@tagged('post_install', '-at_install')
class TestReportsAndMails(TenderManagementTestCommon):
    """Render the PDF reports and the mail templates."""

    def setUp(self):
        super().setUp()
        self.tender = self.create_tender(tender_state='bid_selection')
        self.bid = self.create_bid(self.tender, self.vendor_1, 'qualified')

    def test_tender_reports_render(self):
        with patch('odoo.addons.mail.models.mail_template.MailTemplate.send_mail'):
            self.env['bid.selection'].create({
                'current_tender_id': self.tender.id,
                'tender_bid_id': self.bid.id,
            }).action_confirm_purchase()
        Report = self.env['ir.actions.report']
        tender_html = Report._render_qweb_html(
            'advanced_tender_management.report_tender_management', self.tender.ids)[0].decode()
        self.assertIn('Test Tender', tender_html)
        self.assertIn(self.product_1.name, tender_html)
        bid_html = Report._render_qweb_html(
            'advanced_tender_management.report_tender_bidding', self.bid.ids)[0].decode()
        self.assertIn('Bid Details', bid_html)
        self.assertIn('70.0', bid_html)
        self.assertIn('Vendor One', bid_html)

    def test_mail_templates_render(self):
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.vendor_1.id, 'partner_ref': self.bid.name})
        records = {
            'bid_submission_template': self.bid,
            'bid_edit_request_template': self.bid,
            'bidding_qualified_template': self.bid,
            'bidding_disqualified_template': self.bid,
            'edit_request_approved_template': self.bid,
            'vendor_registration_template': self.vendor_1,
            'approval_user_notification_mail_template': self.vendor_1,
            'purchase_order_confirmed_template': purchase_order,
        }
        for xmlid, record in records.items():
            template = self.env.ref(f'advanced_tender_management.{xmlid}')
            body = template.with_context(bid_link='/odoo/bid', contact_link='/odoo/partner')._render_field(
                'body_html', record.ids)[record.id]
            self.assertTrue(body, xmlid)
        body = self.env.ref('advanced_tender_management.purchase_order_confirmed_template')._render_field(
            'body_html', purchase_order.ids)[purchase_order.id]
        self.assertIn(self.bid.name, body)
