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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Test suite for sale report format editor."""
import logging
from odoo.tests import TransactionCase
from odoo.tools import is_html_empty

_logger = logging.getLogger(__name__)


class TestSaleReportEditor(TransactionCase):
    """Test suite for Sale Report Format Editor module."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for sale report editor tests."""
        super(TestSaleReportEditor, cls).setUpClass()
        _logger.info("Setting up TestSaleReportEditor class")

        # 1. Handle Odoo partner constraints (autopost_bills)
        # This prevents 'NotNullViolation' when creating partners/companies
        cls.env['ir.default'].set('res.partner', 'autopost_bills', 'never')

        # 2. Create Test Company
        cls.test_company = cls.env['res.company'].create({
            'name': 'Test Company',
            'base_layout': 'modern',
            'watermark': True,
            'watermark_show': 'logo',
        })

        # 3. Create a Document Layout
        cls.doc_layout = cls.env['doc.layout'].create({
            'name': 'Test Modern Layout',
            'base_color': '#ff0000',
            'heading_text_color': '#00ff00',
            'logo_position': 'left',
            'customer_position': 'left',
            'company_position': 'right',
            'tagline_position': 'right',
            'company_id': cls.test_company.id,
        })

        # 4. Link layout to company
        cls.test_company.document_layout_id = cls.doc_layout.id

        # 5. Create Partner for Sale Order
        cls.test_partner = cls.env['res.partner'].create({
            'name': 'Test Report Customer',
            'email': 'customer@test.com',
            'street': '123 Test St',
            'city': 'Testville',
        })

        # 6. Create Product for Sale Order Lines
        cls.test_product = cls.env['product.product'].create({
            'name': 'Test Report Product',
            'type': 'consu',
            'list_price': 100.0,
        })

        # 7. Create Sale Order in the test company context
        cls.sale_order = cls.env['sale.order'].with_company(cls.test_company).create({
            'partner_id': cls.test_partner.id,
            'base_layout': 'modern',
            'order_line': [
                (0, 0, {
                    'product_id': cls.test_product.id,
                    'name': 'Test Product Description',
                    'product_uom_qty': 2.0,
                    'price_unit': 100.0,
                })
            ],
        })

        # 8. Report layout for wizard testing
        cls.report_layout = cls.env['report.layout'].search([], limit=1)

        _logger.info("Setup completed successfully")

    def test_01_layout_configuration_link(self):
        """Test sale order theme configuration matches company document layout."""
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
        for layout in ['normal', 'old', 'default', 'modern']:
            self.test_company.base_layout = layout
            self.assertEqual(self.test_company.base_layout, layout)
            self.sale_order.base_layout = layout
            self.assertEqual(self.sale_order.base_layout, layout)

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

        # Update colors, positions, and toggles
        self.doc_layout.write({
            'text_color': '#333333',
            'customer_text_color': '#666666',
            'company_text_color': '#999999',
            'customer_position': 'right',
            'company_position': 'left',
            'tagline_position': 'left',
            'sales_person': False,
            'description': False,
            'tax_value': True,
            'reference': True,
            'source': True,
            'address': True,
            'city': True,
            'country': True,
            'vat': False,
        })
        self.assertEqual(self.doc_layout.text_color, '#333333')
        self.assertEqual(self.doc_layout.customer_text_color, '#666666')
        self.assertEqual(self.doc_layout.company_text_color, '#999999')
        self.assertEqual(self.doc_layout.customer_position, 'right')
        self.assertEqual(self.doc_layout.company_position, 'left')
        self.assertEqual(self.doc_layout.tagline_position, 'left')
        self.assertFalse(self.doc_layout.sales_person)
        self.assertFalse(self.doc_layout.description)
        self.assertTrue(self.doc_layout.tax_value)
        self.assertTrue(self.doc_layout.reference)
        self.assertTrue(self.doc_layout.source)
        self.assertTrue(self.doc_layout.address)
        self.assertTrue(self.doc_layout.city)
        self.assertTrue(self.doc_layout.country)
        self.assertFalse(self.doc_layout.vat)
        _logger.info("test_04_watermark_related_fields Passed Successfully")

    def test_05_base_document_layout_wizard_sync(self):
        """Test the wizard for document layout configuration"""
        _logger.info("Running test_05_base_document_layout_wizard_sync")

        layout = self.report_layout or self.env['report.layout'].search([], limit=1)

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

        # Test changing document_layout_id via wizard
        other_layout = self.env['doc.layout'].create({
            'name': 'Other Layout',
            'company_id': self.test_company.id,
        })
        wizard.document_layout_id = other_layout
        self.assertEqual(self.test_company.document_layout_id, other_layout)

        _logger.info("test_05_base_document_layout_wizard_sync Passed Successfully")

    def test_06_compute_preview_default(self):
        """Test _compute_preview when base_layout is 'default'."""
        _logger.info("Running test_06_compute_preview_default")
        if not self.report_layout:
            self.skipTest("No report layout found")
        self.test_company.base_layout = 'default'
        wizard = self.env['base.document.layout'].with_company(
            self.test_company
        ).create({
            'report_layout_id': self.report_layout.id,
            'base_layout': 'default',
        })
        wizard._compute_preview()
        self.assertTrue(
            wizard.preview,
            "Preview HTML should be generated for default layout",
        )

    def test_07_compute_preview_normal(self):
        """Test _compute_preview when base_layout is 'normal'."""
        _logger.info("Running test_07_compute_preview_normal")
        if not self.report_layout:
            self.skipTest("No report layout found")
        self.test_company.base_layout = 'normal'
        wizard = self.env['base.document.layout'].with_company(
            self.test_company
        ).create({
            'report_layout_id': self.report_layout.id,
            'base_layout': 'normal',
        })
        wizard._compute_preview()
        self.assertTrue(
            wizard.preview,
            "Preview HTML should be generated for normal layout",
        )

    def test_08_compute_preview_modern(self):
        """Test _compute_preview when base_layout is 'modern'."""
        _logger.info("Running test_08_compute_preview_modern")
        if not self.report_layout:
            self.skipTest("No report layout found")
        self.test_company.base_layout = 'modern'
        wizard = self.env['base.document.layout'].with_company(
            self.test_company
        ).create({
            'report_layout_id': self.report_layout.id,
            'base_layout': 'modern',
        })
        wizard._compute_preview()
        self.assertTrue(
            wizard.preview,
            "Preview HTML should be generated for modern layout",
        )

    def test_09_compute_preview_old(self):
        """Test _compute_preview when base_layout is 'old'."""
        _logger.info("Running test_09_compute_preview_old")
        if not self.report_layout:
            self.skipTest("No report layout found")
        self.test_company.base_layout = 'old'
        wizard = self.env['base.document.layout'].with_company(
            self.test_company
        ).create({
            'report_layout_id': self.report_layout.id,
            'base_layout': 'old',
        })
        wizard._compute_preview()
        self.assertTrue(
            wizard.preview,
            "Preview HTML should be generated for old layout",
        )

    def test_10_compute_preview_falsy(self):
        """Test _compute_preview when report_layout_id or base_layout is falsy/unsupported."""
        _logger.info("Running test_10_compute_preview_falsy")
        wizard = self.env['base.document.layout'].with_company(
            self.test_company
        ).create({
            'report_layout_id': False,
        })
        wizard._compute_preview()
        self.assertFalse(
            wizard.preview,
            "Preview should be False when report_layout_id is unset",
        )

        if self.report_layout:
            wizard.report_layout_id = self.report_layout.id
            wizard.base_layout = False
            wizard._compute_preview()
            self.assertFalse(
                wizard.preview,
                "Preview should be False when base_layout is unset",
            )

    def test_11_compute_preview_multi_records(self):
        """Test _compute_preview on a recordset with multiple wizard records."""
        _logger.info("Running test_11_compute_preview_multi_records")
        if not self.report_layout:
            self.skipTest("No report layout found")
        wizard1 = self.env['base.document.layout'].with_company(
            self.test_company
        ).create({
            'report_layout_id': self.report_layout.id,
            'base_layout': 'modern',
        })
        wizard2 = self.env['base.document.layout'].with_company(
            self.test_company
        ).create({
            'report_layout_id': self.report_layout.id,
            'base_layout': 'normal',
        })
        wizards = wizard1 | wizard2
        wizards._compute_preview()
        self.assertTrue(wizard1.preview)
        self.assertTrue(wizard2.preview)

    def test_12_document_layout_save(self):
        """Test document_layout_save method on base.document.layout wizard."""
        _logger.info("Running test_12_document_layout_save")
        wizard = self.env['base.document.layout'].with_company(
            self.test_company
        ).create({})
        # Default behavior: window close action
        action = wizard.document_layout_save()
        self.assertEqual(action.get('type'), 'ir.actions.act_window_close')

        # With report_action in context
        report_action = {'type': 'ir.actions.report', 'report_name': 'test'}
        action_with_ctx = wizard.with_context(report_action=report_action).document_layout_save()
        self.assertEqual(action_with_ctx, report_action)

    def test_13_wizard_onchange_company_id(self):
        """Test _onchange_company_id on base.document.layout wizard."""
        _logger.info("Running test_13_wizard_onchange_company_id")
        wizard = self.env['base.document.layout'].new({
            'company_id': self.test_company.id,
        })
        wizard._onchange_company_id()
        self.assertEqual(wizard.company_id, self.test_company)

    def test_14_wizard_watermark_fields(self):
        """Test watermark and watermark_show fields on base.document.layout wizard."""
        _logger.info("Running test_14_wizard_watermark_fields")
        wizard = self.env['base.document.layout'].with_company(
            self.test_company
        ).create({
            'watermark': True,
            'watermark_show': 'name',
        })
        self.assertTrue(wizard.watermark)
        self.assertEqual(wizard.watermark_show, 'name')

    def test_15_render_sale_reports(self):
        """Test rendering sale order reports across all base layout choices."""
        _logger.info("Running test_15_render_sale_reports")
        ir_ui_view = self.env['ir.ui.view']
        layouts = ['default', 'normal', 'modern', 'old']
        for layout in layouts:
            self.test_company.base_layout = layout
            self.sale_order.base_layout = layout

            # Render sale order raw report template
            rendered_raw = ir_ui_view._render_template(
                'sale.report_saleorder_raw',
                {'docs': self.sale_order},
            )
            self.assertTrue(
                rendered_raw,
                f"Raw report template should render for layout {layout}",
            )

            # Render pro forma report template
            rendered_proforma = ir_ui_view._render_template(
                'sale.report_saleorder_pro_forma',
                {'docs': self.sale_order},
            )
            self.assertTrue(
                rendered_proforma,
                f"Pro-forma report should render for layout {layout}",
            )

    def test_16_render_preview_layout_report(self):
        """Test web.preview_layout_report template override for all base layouts."""
        _logger.info("Running test_16_render_preview_layout_report")
        ir_ui_view = self.env['ir.ui.view']
        layouts = ['default', 'normal', 'modern', 'old']
        for layout in layouts:
            self.test_company.base_layout = layout
            rendered = ir_ui_view._render_template(
                'web.preview_layout_report',
                {
                    'res_company': self.test_company,
                    'company': self.test_company,
                    'is_html_empty': is_html_empty,
                },
            )
            self.assertTrue(
                rendered,
                f"web.preview_layout_report should render for layout {layout}",
            )

    def test_17_render_external_layout_watermark_and_header(self):
        """Test custom_external_layout_standard with watermark and position variations."""
        _logger.info("Running test_17_render_external_layout_watermark_and_header")
        ir_ui_view = self.env['ir.ui.view']

        # Watermark show logo
        self.test_company.write({
            'watermark': True,
            'watermark_show': 'logo',
        })
        self.doc_layout.write({
            'logo_position': 'right',
            'tagline_position': 'left',
            'company_position': 'left',
        })
        rendered_logo = ir_ui_view._render_template(
            'web.external_layout_standard',
            {
                'company': self.test_company,
                'o': self.sale_order,
                'doc': self.sale_order,
                'model': 'sale.order',
            },
        )
        self.assertTrue(rendered_logo)

        # Watermark show name
        self.test_company.write({
            'watermark': True,
            'watermark_show': 'name',
        })
        self.doc_layout.write({
            'logo_position': 'left',
            'tagline_position': 'right',
            'company_position': 'right',
        })
        rendered_name = ir_ui_view._render_template(
            'web.external_layout_standard',
            {
                'company': self.test_company,
                'o': self.sale_order,
                'doc': self.sale_order,
                'model': 'sale.order',
            },
        )
        self.assertTrue(rendered_name)

    def test_18_doc_layout_crud_and_defaults(self):
        """Test doc.layout CRUD operations and default field values."""
        _logger.info("Running test_18_doc_layout_crud_and_defaults")
        new_layout = self.env['doc.layout'].create({
            'name': 'Default Values Check',
        })
        # Check default values
        self.assertTrue(new_layout.sales_person)
        self.assertTrue(new_layout.description)
        self.assertTrue(new_layout.vat)
        self.assertEqual(new_layout.tagline_position, 'right')
        self.assertEqual(new_layout.watermark_show, 'logo')
        self.assertEqual(new_layout.company_id, self.env.company)

        # Update
        new_layout.write({'name': 'Updated Layout Name'})
        self.assertEqual(new_layout.name, 'Updated Layout Name')

        # Unlink
        layout_id = new_layout.id
        new_layout.unlink()
        self.assertFalse(self.env['doc.layout'].browse(layout_id).exists())

    def test_19_demo_doc_layout_records(self):
        """Test that preloaded doc.layout XML records exist and are configured."""
        _logger.info("Running test_19_demo_doc_layout_records")
        modern_ref = self.env.ref(
            'sale_report_format_editor.modern_doc_layout',
            raise_if_not_found=False,
        )
        if modern_ref:
            self.assertEqual(modern_ref.name, 'Modern')
            self.assertEqual(modern_ref.base_color, '#732673')
            self.assertEqual(modern_ref.heading_text_color, '#ffffff')

        standard_ref = self.env.ref(
            'sale_report_format_editor.standard_doc_layout',
            raise_if_not_found=False,
        )
        if standard_ref:
            self.assertEqual(standard_ref.name, 'Standard')
            self.assertEqual(standard_ref.base_color, '#ff7733')
            self.assertEqual(standard_ref.heading_text_color, '#ffffff')
