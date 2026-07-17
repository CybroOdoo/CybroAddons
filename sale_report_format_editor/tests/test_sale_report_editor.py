# -*- coding: utf-8 -*-
# ##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Abhijith CK (odoo@cybrosys.com)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
# ##############################################################################
import logging
from odoo.tests import TransactionCase

_logger = logging.getLogger(__name__)

class TestSaleReportEditor(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestSaleReportEditor, cls).setUpClass()
        _logger.info("Setting up TestSaleReportEditor class")

        # 1. Handle Odoo 19 specific partner constraints (autopost_bills)
        # This prevents 'NotNullViolation' when creating partners/companies
        cls.env['ir.default'].set('res.partner', 'autopost_bills', 'never')

        # 2. Create Test Company
        cls.test_company = cls.env['res.company'].create({
            'name': 'Test Company',
            'base_layout': 'modern',
        })
        # 3. Create a Document Layout
        cls.doc_layout = cls.env['doc.layout'].create({
            'name': 'Test Modern Layout',
            'base_color': '#ff0000',
            'heading_text_color': '#00ff00',
            'logo_position': 'left',
            'company_id': cls.test_company.id,
        })

        # 4. Link layout to company
        cls.test_company.document_layout_id = cls.doc_layout.id

        # 5. Create Partner for Sale Order
        cls.test_partner = cls.env['res.partner'].create({
            'name': 'Test Report Customer',
            'email': 'customer@test.com',
        })

        # 6. Create Sale Order in the test company context
        cls.sale_order = cls.env['sale.order'].with_company(cls.test_company).create({
            'partner_id': cls.test_partner.id,
            'base_layout': 'modern',
        })

        _logger.info("Setup completed successfully")

    def test_01_layout_configuration_link(self):
        _logger.info("Running test_01_layout_configuration_link")

        _logger.info("Actual Theme: %s", self.sale_order.theme_id)
        _logger.info("Expected Theme: %s", self.doc_layout)

        _logger.info("Actual Company: %s", self.sale_order.company_id.name)
        _logger.info("Expected Company: %s", self.test_company.name)

        self.assertEqual(
            self.sale_order.theme_id,
            self.doc_layout,
            "Sale order theme should match the company document layout"
        )

        self.assertEqual(
            self.sale_order.company_id,
            self.test_company,
            "Sale order should belong to the test company"
        )

        _logger.info("Test Passed Successfully")

    def test_02_base_layout_sync(self):
        """Test the base_layout selection values and default"""
        _logger.info("Running test_02_base_layout_sync")
        self.assertEqual(self.test_company.base_layout, 'modern')
        self.assertEqual(self.sale_order.base_layout, 'modern')

        # Change company layout
        self.test_company.base_layout = 'normal'
        self.assertEqual(self.test_company.base_layout, 'normal')
        _logger.info("test_02_base_layout_sync Passed Successfully")

    def test_03_watermark_related_fields(self):
        """Test related fields for watermark between doc.layout and res.company"""
        _logger.info("Running test_03_watermark_related_fields")

        # Set initial values
        self.test_company.watermark = True
        self.test_company.watermark_show = 'logo'

        # Test watermark field (related)
        self.assertTrue(
            self.doc_layout.watermark,
            "Watermark should be True as it is related to company"
        )

        self.doc_layout.watermark = False

        self.assertFalse(
            self.test_company.watermark,
            "Company watermark should become False"
        )

        # Test watermark_show (related)
        self.assertEqual(self.doc_layout.watermark_show, 'logo')

        self.doc_layout.watermark_show = 'name'

        self.assertEqual(
            self.test_company.watermark_show,
            'name',
            "Company watermark_show should match doc layout"
        )

        _logger.info("test_03_watermark_related_fields Passed Successfully")

    def test_04_layout_styling_fields(self):
        """Test that styling fields are correctly saved in doc.layout"""
        _logger.info("Running test_04_layout_styling_fields")
        self.assertEqual(self.doc_layout.base_color, '#ff0000')
        self.assertEqual(self.doc_layout.heading_text_color, '#00ff00')

        # Update colors
        self.doc_layout.write({
            'text_color': '#333333',
            'customer_text_color': '#666666',
        })
        self.assertEqual(self.doc_layout.text_color, '#333333')
        self.assertEqual(self.doc_layout.customer_text_color, '#666666')
        _logger.info("test_04_watermark_related_fields Passed Successfully")

    def test_05_base_document_layout_wizard_sync(self):
        """Test the wizard for document layout configuration"""
        _logger.info("Running test_05_base_document_layout_wizard_sync")

        layout = self.env['report.layout'].search([], limit=1)

        self.assertTrue(layout, "No report layout found")

        wizard = self.env['base.document.layout'].with_company(
            self.test_company
        ).create({
            'report_layout_id': layout.id,
        })

        # Verify related fields in wizard
        self.assertEqual(wizard.base_layout, 'modern')
        self.assertEqual(wizard.document_layout_id, self.doc_layout)

        # Change via wizard
        wizard.base_layout = 'old'

        self.assertEqual(
            self.test_company.base_layout,
            'old'
        )

        _logger.info("test_05_base_document_layout_wizard_sync Passed Successfully")