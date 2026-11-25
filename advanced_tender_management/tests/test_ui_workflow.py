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
from datetime import timedelta

import xlsxwriter

from odoo import Command, fields
from odoo.tests import HttpCase, tagged
from odoo.tools import BinaryBytes

TENDER_ACTION = '/odoo/action-advanced_tender_management.tender_management_action'
BIDDING_ACTION = '/odoo/action-advanced_tender_management.tender_bidding_action'


@tagged('post_install', '-at_install')
class TestTenderUiWorkflow(HttpCase):
    """Click through the tender workflow in the browser: backend forms,
    website bid pages, portal, wizards and imports. The date-driven stage
    changes of the scheduled action are run from Python between tours."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env['ir.config_parameter'].sudo().set_bool(
            'advanced_tender_management.auto_approval', True)
        cls.category = cls.env['tender.category'].create({'name': 'UI Category'})
        cls.gloves = cls.env['product.product'].create({'name': 'UI Gloves'})
        cls.masks = cls.env['product.product'].create({'name': 'UI Masks'})
        cls.responsible = cls.env['res.users'].create({
            'name': 'Tender Responsible', 'login': 'tender_responsible',
            'email': 'responsible@example.com',
        })
        cls.vendor_one = cls.env['res.partner'].create({
            'name': 'UI Vendor One', 'email': 'ui.vendor.one@example.com', 'is_vendor': True,
            'tender_category_ids': [Command.set(cls.category.ids)],
        })
        cls.vendor_two = cls.env['res.partner'].create({
            'name': 'UI Vendor Two', 'email': 'ui.vendor.two@example.com', 'is_vendor': True,
            'tender_category_ids': [Command.set(cls.category.ids)],
        })
        cls.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'UI Vendor One', 'login': 'ui_vendor_one', 'password': 'ui_vendor_one',
            'partner_id': cls.vendor_one.id,
            'group_ids': [Command.set([cls.env.ref('base.group_portal').id])],
        })
        cls.india = cls.env.ref('base.in')
        cls.kerala = cls.env['res.country.state'].search(
            [('country_id', '=', cls.india.id), ('name', '=', 'Kerala')], limit=1)

    def _tender(self, **values):
        today = fields.Date.context_today(self.env.user)
        vals = {
            'name': 'UI Product Tender',
            'responsible_id': self.responsible.id,
            'tender_start_date': today,
            'tender_end_date': today + timedelta(days=10),
            'bid_start_date': today,
            'bid_end_date': today + timedelta(days=5),
            'description': '<p>Tender</p>',
            'tender_category_id': self.category.id,
            'tender_type': 'product_wise_vendor',
            'address_street': '1 Tender Street',
            'address_city': 'Kochi',
            'address_country_id': self.india.id,
            'address_state_id': self.kerala.id,
            'tender_product_line_ids': [
                Command.create({'name': 'Gloves', 'product_id': self.gloves.id,
                                'product_qty': 2.5}),
                Command.create({'name': 'Masks', 'product_id': self.masks.id,
                                'product_qty': 2}),
            ],
        }
        vals.update(values)
        return self.env['tender.management'].create(vals)

    def _close_bidding(self, tender):
        """Let the bidding period end and run the scheduled action."""
        today = fields.Date.context_today(self.env.user)
        tender.write({'bid_start_date': today - timedelta(days=3),
                      'bid_end_date': today - timedelta(days=1)})
        self.env['tender.management'].action_tender_expiration()
        self.assertEqual(tender.tender_state, 'bid_evaluation')

    def _xlsx_attachment(self, name, rows):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        for row_index, row in enumerate(rows):
            for col_index, value in enumerate(row):
                sheet.write(row_index, col_index, value)
        workbook.close()
        self.env['ir.attachment'].create({
            'name': name, 'raw': BinaryBytes(output.getvalue())})

    def test_single_vendor_workflow(self):
        # 1. Create and confirm the tender in the backend
        self.start_tour(TENDER_ACTION, 'tender_ui_create_confirm', login='admin')
        tender = self.env['tender.management'].search([('name', '=', 'UI Tender')])
        self.assertEqual(tender.tender_state, 'confirm')
        self.assertEqual(tender.tender_product_line_ids.mapped('product_qty'), [2.5, 2])

        # 2. Bidding opens on the bid start date
        self.env['tender.management'].action_tender_expiration()
        self.assertEqual(tender.tender_state, 'bid_submission')

        # 3. The tender is listed on the website; vendor one bids there
        self.start_tour('/tender_management', 'tender_ui_website_list', login='ui_vendor_one')
        self.start_tour(f'/show_tender/{tender.id}', 'tender_ui_vendor_bid',
                        login='ui_vendor_one')
        bid_one = self.env['tender.bidding'].search(
            [('tender_id', '=', tender.id), ('vendor_id', '=', self.vendor_one.id)])
        self.assertEqual(bid_one.bidding_state, 'bid_close')
        self.assertAlmostEqual(bid_one.total_bidding_amount, 47.25)
        self.assertEqual(bid_one.vendor_attachments_ids.name, 'bid.pdf')
        self.start_tour('/my/tenders', 'tender_ui_vendor_portal', login='ui_vendor_one')

        # 4. Vendor one asks to edit the bid; the responsible approves
        self.start_tour(f'/show_tender/{tender.id}', 'tender_ui_vendor_edit_request',
                        login='ui_vendor_one')
        self.assertTrue(bid_one.edit_request)
        self.start_tour(f'{BIDDING_ACTION}/{bid_one.id}', 'tender_ui_approve_edit',
                        login='admin')
        self.assertEqual(bid_one.bidding_state, 'bid')

        # 5. Vendor one submits again
        self.start_tour(f'/show_tender/{tender.id}', 'tender_ui_vendor_bid',
                        login='ui_vendor_one')
        self.assertEqual(bid_one.bidding_state, 'bid_close')

        # 6. A bid of vendor two is entered and submitted in the backend
        self.start_tour(f'{BIDDING_ACTION}/new', 'tender_ui_backend_bid', login='admin')
        bid_two = self.env['tender.bidding'].search(
            [('tender_id', '=', tender.id), ('vendor_id', '=', self.vendor_two.id)])
        self.assertEqual(bid_two.bidding_state, 'bid_close')
        self.assertAlmostEqual(bid_two.total_bidding_amount, 45.5)
        self.assertIn(self.vendor_two, tender.registered_vendors_ids)

        # 7. Bidding closes; bids are qualified and the cheapest one bought
        self._close_bidding(tender)
        self.start_tour(f'{TENDER_ACTION}/{tender.id}', 'tender_ui_evaluate_select',
                        login='admin')
        self.assertEqual(tender.tender_state, 'close')
        self.assertEqual(bid_two.bidding_state, 'won')
        self.assertEqual(bid_one.bidding_state, 'lost')
        self.assertEqual(tender.purchase_order_ids.partner_id, self.vendor_two)
        self.assertEqual(tender.purchase_order_ids.state, 'purchase')
        self.assertEqual(tender.purchase_order_ids.order_line.mapped('product_qty'), [2.5, 2])

    def test_product_wise_workflow(self):
        tender = self._tender()
        tender.tender_state = 'bid_submission'
        Bidding = self.env['tender.bidding']
        for vendor, prices in ((self.vendor_one, {self.gloves: 10, self.masks: 9}),
                               (self.vendor_two, {self.gloves: 12, self.masks: 7})):
            Bidding.create({
                'vendor_id': vendor.id, 'tender_id': tender.id,
                'tender_bid_products_ids': Bidding._prepare_bid_line_commands(
                    tender, {str(product.id): price for product, price in prices.items()}),
            }).action_submit_bid()
        self._close_bidding(tender)
        Bidding.search([('tender_id', '=', tender.id)]).action_qualify()

        self.start_tour(f'{TENDER_ACTION}/{tender.id}', 'tender_ui_product_wise', login='admin')
        self.assertEqual(tender.tender_state, 'close')
        orders = tender.purchase_order_ids
        self.assertEqual(orders.partner_id, self.vendor_one | self.vendor_two)
        gloves_order = orders.filtered(lambda order: order.partner_id == self.vendor_one)
        self.assertEqual(gloves_order.order_line.product_id, self.gloves)
        self.assertEqual(gloves_order.order_line.product_qty, 2.5)

    def test_import_product_lines(self):
        tender = self._tender(name='UI Import Tender', tender_type='single_vendor',
                              tender_product_line_ids=[])
        self._xlsx_attachment('ui_tender_import.xlsx', [
            ['Product', 'Description', 'Qty'],
            ['Imported section'],
            ['UI Gloves', 'Imported gloves', 1.5],
        ])
        self.start_tour(f'{TENDER_ACTION}/{tender.id}', 'tender_ui_import_lines', login='admin')
        line = tender.tender_product_line_ids.filtered('product_id')
        self.assertEqual((line.product_id, line.product_qty), (self.gloves, 1.5))

        self._xlsx_attachment('ui_tender_bad_import.xlsx', [
            ['Product', 'Description', 'Qty'],
            ['UI Masks', 'Bad quantity', '5 pcs'],
        ])
        self.start_tour(f'{TENDER_ACTION}/{tender.id}', 'tender_ui_import_bad_quantity',
                        login='admin')
        self.assertFalse(tender.tender_product_line_ids.filtered(
            lambda line: line.name == 'Bad quantity'))

    def test_vendor_registration(self):
        self.start_tour('/vendor_register', 'tender_ui_vendor_register')
        vendor = self.env['res.partner'].search(
            [('email', '=', 'ui.registered.vendor@example.com')])
        self.assertTrue(vendor.is_vendor)
        self.assertEqual(vendor.tender_category_ids, self.category)
        user = self.env['res.users'].search([('partner_id', '=', vendor.id)])
        self.assertTrue(user.has_group('base.group_portal'))
        self.assertEqual(vendor.sudo().signup_type, 'signup')

    def test_dashboard(self):
        self._tender()
        self.start_tour('/odoo/action-advanced_tender_management.tender_dashboard_action',
                        'tender_ui_dashboard', login='admin')
