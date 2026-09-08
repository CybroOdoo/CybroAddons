# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
import logging

from odoo.tests import tagged, TransactionCase


_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'wm_reporting')
class TestWmRevenueReport(TransactionCase):
    """Unit tests verifying billing revenue report aggregations and month-over-month trends."""

    @classmethod
    def setUpClass(cls):
        """
        Set up test class fixtures and environment.
        """
        super().setUpClass()
        cls.category = cls.env['wm.waste.category'].create({'name': 'Plastic Recyclables TestRev'})
        cls.product = cls.env['product.product'].create({
            'name': 'Plastic Scrap TestRev',
            'wm_waste_category_id': cls.category.id,
            'list_price': 2.0,
        })
        cls.partner = cls.env['res.partner'].create({'name': 'Billing Partner TestRev'})
        cls.point = cls.env['wm.collection.point'].create({'name': 'Billing Point TestRev', 'partner_id': cls.partner.id})

        cls.journal = cls.env['account.journal'].search([('type', '=', 'sale'), ('company_id', '=', cls.env.company.id)], limit=1)
        if not cls.journal:
            cls.journal = cls.env['account.journal'].create({
                'name': 'Customer Invoices TestRev',
                'code': 'INVRV',
                'type': 'sale',
                'company_id': cls.env.company.id,
            })

        cls.invoice = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner.id,
            'journal_id': cls.journal.id,
            'invoice_date': '2026-07-28',
        })

        cls.order = cls.env['wm.collection.order'].create({
            'name': 'ORD-REV-001',
            'partner_id': cls.partner.id,
            'collection_point_id': cls.point.id,
            'state': 'completed',
            'company_id': cls.env.company.id,
        })
        cls.line = cls.env['wm.collection.order.line'].create({
            'order_id': cls.order.id,
            'category_id': cls.category.id,
            'product_id': cls.product.id,
            'weight': 100.0,
            'price': 2.0,
            'total_amount': 200.0,
        })

        cls.consolidated = cls.env['wm.consolidated.invoice'].create({
            'partner_id': cls.partner.id,
            'company_id': cls.env.company.id,
            'order_ids': [(6, 0, [cls.order.id])],
            'invoice_id': cls.invoice.id,
            'state': 'invoiced',
        })
        cls.order.consolidated_invoice_id = cls.consolidated.id

    def test_revenue_report_revenue_per_kg(self):
        """
        Test that revenue report revenue per kg behaves as expected.
        """
        reports = self.env['wm.revenue.report'].search([
            ('waste_category_id', '=', self.category.id)
        ])
        self.assertTrue(reports, "Revenue report record should be created")
        report = reports[0]
        self.assertEqual(report.invoiced_amount, 200.0)
        self.assertEqual(report.weight_kg, 100.0)
        self.assertEqual(report.revenue_per_kg, 2.0, "Revenue per kg should be 200/100 = 2.0")
        _logger.info('PASS: test_revenue_report_revenue_per_kg')

    def test_revenue_report_multicompany(self):
        """
        Test that revenue report multicompany behaves as expected.
        """
        comp2 = self.env['res.company'].create({'name': 'Billing Company 2 TestRev'})
        partner2 = self.env['res.partner'].create({'name': 'Billing Partner Comp2 TestRev'})
        point2 = self.env['wm.collection.point'].create({'name': 'Billing Point Comp2', 'partner_id': partner2.id})
        journal2 = self.env['account.journal'].search([('type', '=', 'sale'), ('company_id', '=', comp2.id)], limit=1)
        if not journal2:
            journal2 = self.env['account.journal'].create({
                'name': 'Customer Invoices Comp2 TestRev',
                'code': 'INV2R',
                'type': 'sale',
                'company_id': comp2.id,
            })
        inv2 = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': partner2.id,
            'company_id': comp2.id,
            'journal_id': journal2.id,
        })

        ord2 = self.env['wm.collection.order'].create({
            'name': 'ORD-REV-COMP2',
            'partner_id': partner2.id,
            'collection_point_id': point2.id,
            'state': 'completed',
            'company_id': comp2.id,
        })
        self.env['wm.collection.order.line'].create({
            'order_id': ord2.id,
            'category_id': self.category.id,
            'product_id': self.product.id,
            'weight': 50.0,
            'price': 4.0,
            'total_amount': 200.0,
        })

        cons2 = self.env['wm.consolidated.invoice'].create({
            'partner_id': partner2.id,
            'company_id': comp2.id,
            'order_ids': [(6, 0, [ord2.id])],
            'invoice_id': inv2.id,
            'state': 'invoiced',
        })
        ord2.consolidated_invoice_id = cons2.id

        reports_c1 = self.env['wm.revenue.report'].search([('company_id', '=', self.env.company.id), ('waste_category_id', '=', self.category.id)])
        reports_c2 = self.env['wm.revenue.report'].search([('company_id', '=', comp2.id), ('waste_category_id', '=', self.category.id)])

        self.assertEqual(sum(reports_c1.mapped('weight_kg')), 100.0)
        self.assertEqual(sum(reports_c2.mapped('weight_kg')), 50.0)
        _logger.info('PASS: test_revenue_report_multicompany')
