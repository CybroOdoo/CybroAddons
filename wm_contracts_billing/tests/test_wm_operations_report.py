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
class TestWmOperationsReport(TransactionCase):
    """Unit tests verifying cross-module operations overview reporting metrics."""

    @classmethod
    def setUpClass(cls):
        """
        Set up test class fixtures and environment.
        """
        super().setUpClass()
        cls.category = cls.env['wm.waste.category'].create({'name': 'Electronic Waste TestOps'})
        cls.product = cls.env['product.product'].create({
            'name': 'E-Waste Scrap TestOps',
            'wm_waste_category_id': cls.category.id,
            'list_price': 10.0,
        })
        cls.partner = cls.env['res.partner'].create({'name': 'Operations Customer TestOps'})
        cls.point = cls.env['wm.collection.point'].create({'name': 'Ops Point TestOps', 'partner_id': cls.partner.id})

        cls.journal = cls.env['account.journal'].search([('type', '=', 'sale'), ('company_id', '=', cls.env.company.id)], limit=1)
        if not cls.journal:
            cls.journal = cls.env['account.journal'].create({
                'name': 'Customer Invoices Ops TestOps',
                'code': 'INVOO',
                'type': 'sale',
                'company_id': cls.env.company.id,
            })

        cls.invoice = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner.id,
            'journal_id': cls.journal.id,
        })

        cls.order = cls.env['wm.collection.order'].create({
            'name': 'ORD-OPS-001',
            'partner_id': cls.partner.id,
            'collection_point_id': cls.point.id,
            'state': 'completed',
        })
        cls.line = cls.env['wm.collection.order.line'].create({
            'order_id': cls.order.id,
            'category_id': cls.category.id,
            'product_id': cls.product.id,
            'weight': 80.0,
            'price': 10.0,
            'total_amount': 800.0,
        })

        cls.consolidated = cls.env['wm.consolidated.invoice'].create({
            'partner_id': cls.partner.id,
            'order_ids': [(6, 0, [cls.order.id])],
            'invoice_id': cls.invoice.id,
            'state': 'invoiced',
        })
        cls.order.consolidated_invoice_id = cls.consolidated.id

    def test_operations_report_combined_metrics(self):
        """
        Test that operations report combined metrics behaves as expected.
        """
        reports = self.env['wm.operations.report'].search([
            ('waste_category_id', '=', self.category.id)
        ])
        self.assertTrue(reports, "Operations Overview report row should exist")
        report = reports[0]
        self.assertEqual(report.weight_kg, 80.0, "Operational measure weight_kg should be 80.0")
        self.assertEqual(report.invoiced_amount, 800.0, "Financial measure invoiced_amount should be 800.0")
        _logger.info('PASS: test_operations_report_combined_metrics')
