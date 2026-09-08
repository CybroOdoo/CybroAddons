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
class TestWmCollectionReport(TransactionCase):
    """Unit tests verifying collection order operational report calculations."""

    @classmethod
    def setUpClass(cls):
        """
        Set up test class fixtures and environment.
        """
        super().setUpClass()
        cls.category = cls.env['wm.waste.category'].create({'name': 'Test General Waste TestCollRep'})
        cls.product = cls.env['product.product'].create({
            'name': 'Test Waste Product TestCollRep',
            'wm_waste_category_id': cls.category.id,
        })
        cls.partner = cls.env['res.partner'].create({'name': 'Test Partner TestCollRep'})
        cls.point = cls.env['wm.collection.point'].create({'name': 'Test Point TestCollRep', 'partner_id': cls.partner.id})

        cls.order = cls.env['wm.collection.order'].create({
            'name': 'ORD-TEST-001',
            'partner_id': cls.partner.id,
            'collection_point_id': cls.point.id,
            'state': 'completed',
            'company_id': cls.env.company.id,
        })
        cls.line = cls.env['wm.collection.order.line'].create({
            'order_id': cls.order.id,
            'category_id': cls.category.id,
            'product_id': cls.product.id,
            'weight': 150.0,
        })

    def test_collection_report_aggregates(self):
        """
        Test that collection report aggregates behaves as expected.
        """
        reports = self.env['wm.collection.report'].search([
            ('waste_category_id', '=', self.category.id)
        ])
        self.assertTrue(reports, "Collection report record should be returned by SQL view")
        total_weight = sum(reports.mapped('weight_kg'))
        self.assertEqual(total_weight, 150.0, "Total aggregated weight_kg should match fixture data")
        _logger.info('PASS: test_collection_report_aggregates')

    def test_collection_report_multicompany(self):
        """
        Test that collection report multicompany behaves as expected.
        """
        company_2 = self.env['res.company'].create({'name': 'Company 2 TestCollRep'})
        order_comp2 = self.env['wm.collection.order'].create({
            'name': 'ORD-TEST-COMP2',
            'partner_id': self.partner.id,
            'collection_point_id': self.point.id,
            'state': 'completed',
            'company_id': company_2.id,
        })
        self.env['wm.collection.order.line'].create({
            'order_id': order_comp2.id,
            'category_id': self.category.id,
            'product_id': self.product.id,
            'weight': 200.0,
        })

        reports_comp1 = self.env['wm.collection.report'].search([
            ('company_id', '=', self.env.company.id),
            ('waste_category_id', '=', self.category.id)
        ])
        reports_comp2 = self.env['wm.collection.report'].search([
            ('company_id', '=', company_2.id),
            ('waste_category_id', '=', self.category.id)
        ])
        self.assertEqual(sum(reports_comp1.mapped('weight_kg')), 150.0)
        self.assertEqual(sum(reports_comp2.mapped('weight_kg')), 200.0)
        _logger.info('PASS: test_collection_report_multicompany')
