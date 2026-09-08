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
class TestWmWeightRevenueReport(TransactionCase):
    """Unit tests verifying weight-to-revenue reporting metrics and billing reconciliation."""

    @classmethod
    def setUpClass(cls):
        """
        Set up test class fixtures and environment.
        """
        super().setUpClass()
        cls.category = cls.env['wm.waste.category'].create({'name': 'Organic Waste TestWeightRev'})
        cls.product = cls.env['product.product'].create({
            'name': 'Compostable Material TestWeightRev',
            'wm_waste_category_id': cls.category.id,
        })
        cls.partner = cls.env['res.partner'].create({'name': 'Uninvoiced Customer TestWeightRev'})

        # Order 1: Completed state, NO consolidated invoice (billing skip-out case)
        cls.uninvoiced_order = cls.env['wm.collection.order'].create({
            'name': 'ORD-UNINVOICED-001',
            'partner_id': cls.partner.id,
            'state': 'completed',
            'consolidated_invoice_id': False,
        })
        cls.env['wm.collection.order.line'].create({
            'order_id': cls.uninvoiced_order.id,
            'category_id': cls.category.id,
            'product_id': cls.product.id,
            'weight': 300.0,
            'price': 1.5,
            'total_amount': 450.0,
        })

    def test_left_join_uninvoiced_order_surfaced(self):
        """
        Test that left join uninvoiced order surfaced behaves as expected.
        """
        reports = self.env['wm.weight.revenue.report'].search([
            ('order_id', '=', self.uninvoiced_order.id)
        ])
        self.assertTrue(reports, "Completed order without consolidated invoice MUST appear in Weight to Revenue report via LEFT JOIN")
        report = reports[0]
        self.assertEqual(report.weight_kg, 300.0, "Weight should be included")
        self.assertEqual(report.uninvoiced_amount, 450.0, "Uninvoiced amount should be 450.0 for unbilled order")
        self.assertEqual(report.uninvoiced_order_count, 1, "Uninvoiced order count should be 1")
        _logger.info('PASS: test_left_join_uninvoiced_order_surfaced')
