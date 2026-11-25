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
from datetime import date, timedelta
from unittest.mock import patch

from odoo.exceptions import UserError, ValidationError

from odoo.tests import tagged

from .common import TenderManagementTestCommon


@tagged('post_install', '-at_install')
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
        self.create_bid(self.tender, self.vendor_1, 'qualified')
        bid_2 = self.create_bid(self.tender, self.vendor_2, 'disqualified', {
            self.product_1.id: 0,
            self.product_2.id: 10,
        })
        bid_2.edit_request = True
        self.tender.tender_state = 'bid_submission'

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

        self.tender.tender_state = 'bid_selection'
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

    def test_stage_buttons_follow_the_workflow(self):
        tender = self.tender
        with self.assertRaises(UserError):
            tender.action_bid_evaluation()
        tender.action_confirm_tender()
        self.assertEqual(tender.tender_state, 'confirm')
        with self.assertRaises(UserError):
            tender.action_start_selection()
        tender.tender_state = 'bid_submission'
        tender.action_bid_evaluation()
        self.assertEqual(tender.tender_state, 'bid_evaluation')
        with self.assertRaises(UserError):
            tender.action_close()
        tender.action_start_selection()
        self.assertEqual(tender.tender_state, 'bid_selection')
        tender.action_close()
        self.assertEqual(tender.tender_state, 'close')
        with self.assertRaises(UserError):
            tender.action_cancel()
        with self.assertRaises(UserError):
            tender.action_select_final_bid()

    def test_cancel_from_open_stages(self):
        for state in ('draft', 'confirm', 'bid_submission', 'bid_evaluation', 'bid_selection'):
            tender = self.create_tender(name=f'Cancel {state}', tender_state=state)
            tender.action_cancel()
            self.assertEqual(tender.tender_state, 'cancel')
        with self.assertRaises(UserError):
            tender.action_cancel()

    def test_confirm_bids_needs_a_selected_line(self):
        self.tender.write({'tender_type': 'product_wise_vendor', 'tender_state': 'bid_selection'})
        self.create_bid(self.tender, self.vendor_1, 'qualified')
        with self.assertRaises(UserError):
            self.tender.action_confirm_bids()
        self.assertEqual(self.tender.tender_state, 'bid_selection')

    def test_state_transitions_and_expiration(self):

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
        self.tender.write({'tender_type': 'product_wise_vendor', 'tender_state': 'bid_selection'})
        bid = self.create_bid(self.tender, self.vendor_1, 'qualified')
        line = bid.tender_bid_products_ids.filtered(lambda line: line.product_id == self.product_1)
        line.action_confirm_bid()

        with patch('odoo.addons.mail.models.mail_template.MailTemplate.send_mail'):
            self.tender.action_confirm_bids()

        self.assertTrue(self.tender.purchase_confirmed)
        self.assertEqual(self.tender.tender_state, 'close')
        self.assertEqual(bid.bidding_state, 'won')
        self.assertEqual(len(self.tender.purchase_order_ids), 1)
        self.assertEqual(self.tender.purchase_order_ids.partner_id, self.vendor_1)

    def test_product_template_xlsx_lists_sections_and_products(self):
        self.tender.tender_product_line_ids = [(0, 0, {
            'name': 'Civil Works', 'display_type': 'line_section'})]
        content = self.tender._get_product_template_xlsx()
        self.assertTrue(content.startswith(b'PK'))

    def test_confirm_bids_ignores_other_tenders(self):
        self.tender.write({'tender_type': 'product_wise_vendor', 'tender_state': 'bid_selection'})
        other = self.create_tender(name='Other', tender_type='product_wise_vendor',
                                   tender_state='bid_selection')
        other_line = self.create_bid(other, self.vendor_2, 'qualified').tender_bid_products_ids[:1]
        other_line.action_confirm_bid()
        own_line = self.create_bid(self.tender, self.vendor_1, 'qualified').tender_bid_products_ids[:1]
        own_line.action_confirm_bid()
        losing_bid = self.create_bid(self.tender, self.vendor_2, 'qualified')

        with patch('odoo.addons.mail.models.mail_template.MailTemplate.send_mail'):
            self.tender.action_confirm_bids()

        self.assertEqual(self.tender.purchase_order_ids.partner_id, self.vendor_1)
        self.assertEqual(self.tender.purchase_order_ids.order_line.product_id, own_line.product_id)
        self.assertFalse(other.purchase_order_ids)
        self.assertEqual(own_line.tender_bidding_id.bidding_state, 'won')
        self.assertEqual(losing_bid.bidding_state, 'lost')
        self.assertEqual(other_line.tender_bidding_id.bidding_state, 'pre_qualification')

    def test_dashboard_category_and_type_figures(self):
        details = self.tender.get_tender_details()
        categories = details['tender_category_data']
        self.assertEqual(categories['category_type_count'][
            categories['category_types'].index(self.category.name)], 1)
        self.assertEqual(details['tender_type_data']['tender_type_count'], [1, 0])
        self.assertEqual(details['tender_timeline_data']['tender_timeline_data'], [5])
        self.assertEqual(details['tender_location_count'], 1)
