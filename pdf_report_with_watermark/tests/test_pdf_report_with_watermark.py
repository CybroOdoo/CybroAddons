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
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestPdfReportWithWatermark(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        # Minimal 1x1 transparent PNG in base64
        cls.sample_image_b64 = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        )

    def test_default_watermark_settings(self):
        """Test default values for watermark fields on company."""
        self.assertFalse(self.company.watermark, "Watermark should be disabled by default")
        self.assertEqual(self.company.watermark_type, 'text', "Default watermark type should be text")
        self.assertEqual(self.company.font_size, 20, "Default font size should be 20")

    def test_text_watermark_configuration_and_rendering(self):
        """Test text watermark configuration and report template rendering."""
        self.company.write({
            'watermark': True,
            'watermark_type': 'text',
            'content_text': 'CONFIDENTIAL',
            'color_picker': '#FF0000',
            'font_size': 36,
            'rotating_angle': 45.0,
        })

        html = self.env['ir.qweb']._render('web.external_layout_body', {'company': self.company})
        self.assertIn('class="watermark"', html, "Watermark container must be rendered")
        self.assertIn('CONFIDENTIAL', html, "Watermark text must be rendered")
        self.assertIn('#FF0000', html, "Watermark color must be applied")
        self.assertIn('36px', html, "Font size must be applied")
        self.assertIn('rotate(-45.0deg)', html, "Rotation angle must be applied")

    def test_watermark_disabled_rendering(self):
        """Test that disabled watermark is completely omitted from the report output."""
        self.company.write({
            'watermark': False,
            'content_text': 'SHOULD_NOT_APPEAR',
        })
        html = self.env['ir.qweb']._render('web.external_layout_body', {'company': self.company})
        self.assertNotIn('class="watermark"', html, "Watermark container must not be rendered when disabled")
        self.assertNotIn('SHOULD_NOT_APPEAR', html)

    def test_image_watermark_rendering(self):
        """Test image watermark configuration and data URI generation in template."""
        self.company.write({
            'watermark': True,
            'watermark_type': 'image',
            'background_image': self.sample_image_b64,
            'rotating_angle': 30.0,
        })

        html = self.env['ir.qweb']._render('web.external_layout_body', {'company': self.company})
        self.assertIn('class="watermark"', html)
        self.assertIn('data:image/png;base64', html, "Background image data URI must be rendered")
        self.assertIn('rotate(-30.0deg)', html)

    def test_logo_watermark_rendering(self):
        """Test logo watermark configuration and rendering in template."""
        self.company.write({
            'watermark': True,
            'watermark_type': 'logo',
            'logo': self.sample_image_b64,
            'rotating_angle': 15.0,
        })

        html = self.env['ir.qweb']._render('web.external_layout_body', {'company': self.company})
        self.assertIn('class="watermark"', html)
        self.assertIn('data:image/png;base64', html, "Company logo data URI must be rendered")
        self.assertIn('rotate(-15.0deg)', html)

    def test_document_layout_wizard_sync(self):
        """Test bidirectional reading and writing between document layout wizard and res.company."""
        wizard = self.env['base.document.layout'].create({})
        self.assertEqual(wizard.watermark, self.company.watermark)

        # Write to wizard with readonly=False fields and assert writeback to company
        wizard.write({
            'watermark': True,
            'watermark_type': 'text',
            'content_text': 'ORIGINAL_COPY',
            'font_size': 28,
            'color_picker': '#0000FF',
            'rotating_angle': 60.0,
        })

        self.assertTrue(self.company.watermark, "Watermark enable state must write back to company")
        self.assertEqual(self.company.content_text, 'ORIGINAL_COPY', "Watermark text must write back to company")
        self.assertEqual(self.company.font_size, 28, "Font size must write back to company")
        self.assertEqual(self.company.color_picker, '#0000FF', "Color picker must write back to company")
        self.assertEqual(self.company.rotating_angle, 60.0, "Rotation angle must write back to company")

    def test_multi_company_watermark_isolation(self):
        """Test that watermark configurations on one company do not leak to another company."""
        company_b = self.env['res.company'].create({
            'name': 'Second Test Company',
            'watermark': False,
        })
        self.company.write({
            'watermark': True,
            'content_text': 'COMPANY_A_TEXT',
        })

        self.assertTrue(self.company.watermark)
        self.assertFalse(company_b.watermark, "Company B watermark should remain disabled")

        html_b = self.env['ir.qweb']._render('web.external_layout_body', {'company': company_b})
        self.assertNotIn('class="watermark"', html_b, "Company B reports should not include watermark")
        self.assertNotIn('COMPANY_A_TEXT', html_b)

    def test_views_architecture_get_view(self):
        """Test that extended views load and parse without XML or xpath errors."""
        layout_view = self.env['base.document.layout'].get_view(
            view_id=self.env.ref('pdf_report_with_watermark.view_base_document_layout_inherit_pdf_report_with_watermark').id,
            view_type='form'
        )
        self.assertIn('watermark', layout_view['arch'])
        self.assertIn('rotating_angle', layout_view['arch'])

        company_view = self.env['res.company'].get_view(
            view_id=self.env.ref('pdf_report_with_watermark.res_company_view_form_inherit_pdf_report_with_watermark').id,
            view_type='form'
        )
        self.assertIn('watermark_config', company_view['arch'])
