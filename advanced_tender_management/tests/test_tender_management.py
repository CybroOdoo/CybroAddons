# -*- coding: utf-8 -*-
import json
from datetime import date, timedelta
from io import BytesIO
from unittest.mock import patch

from odoo.exceptions import ValidationError

from .common import TenderManagementTestCommon


class _Stream:
    def __init__(self):
        self.buffer = BytesIO()

    def write(self, data):
        self.buffer.write(data)


class _Response:
    def __init__(self):
        self.stream = _Stream()


class TestTenderManagement(TenderManagementTestCommon):
    """Tests for tender management workflows."""

    def setUp(self):
        super().setUp()
        self.tender = self.create_tender()

    def test_date_constraints(self):
        with self.assertRaises(ValidationError):
            self.create_tender(
                tender_end_date=date.today() - timedelta(days=1),
            )
        with self.assertRaises(ValidationError):
            self.create_tender(
                bid_start_date=date.today() + timedelta(days=3),
                bid_end_date=date.today() + timedelta(days=2),
            )

    def test_counts_and_dashboard_details(self):
        bid_1 = self.create_bid(self.tender, self.vendor_1, 'qualified')
        bid_2 = self.create_bid(self.tender, self.vendor_2, 'disqualified', {
            self.product_1.id: 0,
            self.product_2.id: 10,
        })
        bid_2.edit_request = True
        self.tender.tender_state = 'bid_submission'

        self.tender._compute_all_bid_count()
        self.tender._compute_qualified_bid_count()
        self.tender._compute_evaluation_bid_count()
        self.tender._compute_legit_bid_count()
        details = self.tender.get_tender_details()

        self.assertEqual(self.tender.all_bid_count, 2)
        self.assertEqual(self.tender.qualified_bid_count, 1)
        self.assertEqual(self.tender.evaluation_bid_count, 1)
        self.assertEqual(self.tender.legit_bid_count, 1)
        self.assertEqual(details['tender_count'], 1)
        self.assertEqual(details['vendors_count'], 2)
        self.assertEqual(details['qualified_bid_count'], 1)
        self.assertEqual(details['disqualified_bid_count'], 1)
        self.assertEqual(details['edit_request_count'], 1)
        self.assertEqual(details['pre_qualification_count'], 0)

    def test_action_select_final_bid_and_window_actions(self):
        cheaper_bid = self.create_bid(self.tender, self.vendor_2, 'qualified', {
            self.product_1.id: 1,
            self.product_2.id: 1,
        })
        self.create_bid(self.tender, self.vendor_1, 'qualified')

        action = self.tender.action_select_final_bid()

        self.assertEqual(self.tender.best_bid_id, cheaper_bid)
        self.assertEqual(action['res_model'], 'bid.selection')
        self.assertEqual(action['context']['default_tender_bid_id'], cheaper_bid.id)
        self.assertEqual(self.tender.action_get_purchase_order()['res_model'], 'purchase.order')
        self.assertEqual(self.tender.action_get_bids()['res_model'], 'tender.bidding')
        self.assertEqual(self.tender.action_get_qualified_bids()['name'], 'Qualified Bids')
        self.assertEqual(self.tender.action_get_legit_bids()['name'], 'Legit Bids')
        self.assertEqual(self.tender.action_get_evaluation_bids()['res_model'], 'tender.bidding.product.lines')
        self.assertEqual(
            self.tender.action_import_tender_product_wizard()['res_model'],
            'import.tender.product.line',
        )

    def test_state_transitions_and_expiration(self):
        self.tender.action_confirm_tender()
        self.tender.action_bid_evaluation()
        self.assertEqual(self.tender.tender_state, 'bid_evaluation')

        tender_today = self.create_tender(
            name='Tender Today',
            bid_start_date=date.today(),
            bid_end_date=date.today() + timedelta(days=1),
        )
        tender_expired = self.create_tender(
            name='Tender Expired',
            bid_start_date=date.today() - timedelta(days=2),
            bid_end_date=date.today() - timedelta(days=1),
        )
        (tender_today | tender_expired).write({'tender_state': 'confirm'})

        self.env['tender.management'].action_tender_expiration()

        self.assertEqual(tender_today.tender_state, 'bid_submission')
        self.assertEqual(tender_expired.tender_state, 'bid_evaluation')

    def test_action_confirm_bids_creates_purchase_orders(self):
        self.tender.tender_type = 'product_wise_vendor'
        bid = self.create_bid(self.tender, self.vendor_1, 'qualified')
        line = bid.tender_bid_products_ids.filtered(lambda l: l.product_id == self.product_1)
        line.action_confirm_bid()

        with patch('odoo.addons.mail.models.mail_template.MailTemplate.send_mail'):
            self.tender.action_confirm_bids()

        self.assertTrue(self.tender.purchase_confirmed)
        self.assertEqual(len(self.tender.purchase_order_ids), 1)
        self.assertEqual(self.tender.purchase_order_ids.partner_id, self.vendor_1)

    def test_xlsx_actions_and_report_generation(self):
        action = self.tender.action_print_xlsx_report()
        options = json.loads(action['data']['options'])
        response = _Response()

        self.tender.get_xlsx_report(options, response)

        self.assertEqual(action['report_type'], 'xlsx')
        self.assertTrue(response.stream.buffer.getvalue())
