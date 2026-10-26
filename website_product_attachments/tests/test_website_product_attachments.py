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
from odoo.tests import HttpCase, TransactionCase, tagged

# Minimal valid (unencrypted) PDF. Real PDF content is needed because other
# modules (e.g. sale_pdf_quote_builder) parse every PDF attachment linked
# to a product and reject invalid files.
VALID_PDF = (
    b'%PDF-1.3\n%\xe2\xe3\xcf\xd3\n'
    b'1 0 obj\n<<\n/Producer (pypdf)\n>>\nendobj\n'
    b'2 0 obj\n<<\n/Type /Pages\n/Count 1\n/Kids [ 4 0 R ]\n>>\nendobj\n'
    b'3 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n'
    b'4 0 obj\n<<\n/Type /Page\n/Resources <<\n>>\n'
    b'/MediaBox [ 0.0 0.0 72 72 ]\n/Parent 2 0 R\n>>\nendobj\n'
    b'xref\n0 5\n'
    b'0000000000 65535 f \n0000000015 00000 n \n0000000054 00000 n \n'
    b'0000000113 00000 n \n0000000162 00000 n \n'
    b'trailer\n<<\n/Size 5\n/Root 3 0 R\n/Info 1 0 R\n>>\n'
    b'startxref\n254\n%%EOF\n'
)


@tagged('post_install', '-at_install')
class TestWebsiteProductAttachments(TransactionCase):
    """Unit tests for website_product_attachments module:
    validates manifest dependencies, view inheritance, template structure,
    and the controller attachment search domain.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.template'].create({
            'name': 'Test Attachment Product',
            'list_price': 50.0,
            'is_published': True,
        })
        cls.other_product = cls.env['product.template'].create({
            'name': 'Other Product Without Attachment',
            'list_price': 30.0,
            'is_published': True,
        })

        # Valid binary attachment for cls.product
        cls.attachment_binary = cls.env['ir.attachment'].create({
            'name': 'User Manual PDF',
            'type': 'binary',
            'raw': VALID_PDF,
            'mimetype': 'application/pdf',
            'res_model': 'product.template',
            'res_id': cls.product.id,
            'access_token': False,
        })

        # Valid URL attachment for cls.product
        cls.attachment_url = cls.env['ir.attachment'].create({
            'name': 'External Documentation Link',
            'type': 'url',
            'url': 'https://example.com/docs/product-manual',
            'res_model': 'product.template',
            'res_id': cls.product.id,
            'access_token': False,
        })

        # Attachment with access_token (should be excluded by search domain)
        cls.attachment_with_token = cls.env['ir.attachment'].create({
            'name': 'Restricted Internal Document',
            'type': 'binary',
            'raw': b'Internal document content',
            'res_model': 'product.template',
            'res_id': cls.product.id,
            'access_token': 'secret-token-12345',
        })

        # Attachment belonging to another product
        cls.attachment_other_product = cls.env['ir.attachment'].create({
            'name': 'Other Product Attachment',
            'type': 'binary',
            'raw': b'Other product file',
            'res_model': 'product.template',
            'res_id': cls.other_product.id,
            'access_token': False,
        })

        # Attachment belonging to another model
        cls.attachment_other_model = cls.env['ir.attachment'].create({
            'name': 'Partner Attachment',
            'type': 'binary',
            'raw': b'Partner file content',
            'res_model': 'res.partner',
            'res_id': cls.env.user.partner_id.id,
            'access_token': False,
        })

    def test_01_manifest_dependencies(self):
        """Verify module manifest dependencies:
        Confirm website_sale is declared, installed, and no unused dependencies exist.
        """
        module = self.env['ir.module.module'].search([
            ('name', '=', 'website_product_attachments')
        ], limit=1)
        self.assertTrue(module, "Module website_product_attachments should be found in registry.")

        # Inspect manifest dependencies
        declared_dependencies = [dep.name for dep in module.dependencies_id]
        self.assertIn(
            'website_sale',
            declared_dependencies,
            "website_sale must be declared in depends since controller and views extend it."
        )

        # Check whether any declared dependency is unused
        # 'website_sale' is directly utilized in views/website_sale_templates.xml
        # and controllers/website_product_attachments.py
        view = self.env.ref('website_product_attachments.product_attachments', raise_if_not_found=False)
        self.assertTrue(view, "Inherited view website_product_attachments.product_attachments should exist.")
        self.assertEqual(
            view.inherit_id.xml_id,
            'website_sale.cta_wrapper',
            "View must inherit from website_sale.cta_wrapper."
        )

    def test_02_view_structure(self):
        """Verify the inherited view architecture contains expected classes and elements."""
        view = self.env.ref('website_product_attachments.product_attachments')
        self.assertTrue(view.active, "View product_attachments should be active by default.")
        arch = view.arch
        self.assertIn(
            'js_attachment_container',
            arch,
            "Template arch should define the container .js_attachment_container."
        )
        self.assertIn(
            'Related Documents:',
            arch,
            "Template arch should include 'Related Documents:' header label."
        )
        self.assertIn(
            'js_on_click_show_attachment',
            arch,
            "Template arch should include download click class .js_on_click_show_attachment."
        )
        self.assertIn(
            't-att-data-value="attachment.id"',
            arch,
            "Template arch should pass attachment id in data-value."
        )
        self.assertIn(
            't-out="attachment.name"',
            arch,
            "Template arch should render attachment name using t-out."
        )

    def test_03_attachment_search_domain_filtering(self):
        """Verify the controller's attachment search domain:
        Only attachments with res_model='product.template', matching res_id,
        and access_token=False must be fetched.
        """
        domain = [
            ('res_model', '=', 'product.template'),
            ('res_id', '=', self.product.id),
            ('access_token', '=', False),
        ]
        found_attachments = self.env['ir.attachment'].sudo().search(domain, order='id')

        # Should only contain attachment_binary and attachment_url
        self.assertEqual(len(found_attachments), 2)
        self.assertIn(self.attachment_binary, found_attachments)
        self.assertIn(self.attachment_url, found_attachments)

        # Exclusions
        self.assertNotIn(
            self.attachment_with_token,
            found_attachments,
            "Attachment with access_token set must not be returned."
        )
        self.assertNotIn(
            self.attachment_other_product,
            found_attachments,
            "Attachment belonging to another product must not be returned."
        )
        self.assertNotIn(
            self.attachment_other_model,
            found_attachments,
            "Attachment belonging to another model must not be returned."
        )


@tagged('post_install', '-at_install')
class TestWebsiteProductAttachmentsHttp(HttpCase):
    """End-to-end HTTP integration tests for product page attachment display
    and the /attachment/download route.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.template'].create({
            'name': 'HTTP Test Product With Attachment',
            'list_price': 99.0,
            'is_published': True,
        })
        cls.product_no_att = cls.env['product.template'].create({
            'name': 'HTTP Test Product Without Attachment',
            'list_price': 49.0,
            'is_published': True,
        })

        cls.binary_data = VALID_PDF
        cls.attachment_pdf = cls.env['ir.attachment'].create({
            'name': 'Product-Manual.pdf',
            'type': 'binary',
            'raw': cls.binary_data,
            'mimetype': 'application/pdf',
            'res_model': 'product.template',
            'res_id': cls.product.id,
            'access_token': False,
        })

        cls.attachment_link = cls.env['ir.attachment'].create({
            'name': 'Online Specification',
            'type': 'url',
            'url': 'https://example.com/specifications',
            'res_model': 'product.template',
            'res_id': cls.product.id,
            'access_token': False,
        })

        cls.attachment_empty_url = cls.env['ir.attachment'].create({
            'name': 'Empty URL Document',
            'type': 'url',
            'url': False,
            'res_model': 'product.template',
            'res_id': cls.product.id,
            'access_token': False,
        })

        cls.env.flush_all()

    def test_05_http_product_page_shows_attachments(self):
        """Access product page via HTTP and verify attachment elements are in HTML."""
        url = self.product.website_url
        response = self.url_open(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Related Documents:',
            response.text,
            "Product page should display 'Related Documents:' when attachments exist."
        )
        self.assertIn('Product-Manual.pdf', response.text)
        self.assertIn('Online Specification', response.text)
        self.assertIn(f'data-value="{self.attachment_pdf.id}"', response.text)

    def test_06_http_product_page_without_attachments(self):
        """Access product page without attachments and verify no attachment block is shown."""
        url = self.product_no_att.website_url
        response = self.url_open(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(
            'Related Documents:',
            response.text,
            "Product page without attachments must not show 'Related Documents:'."
        )

    def test_07_download_attachment_binary(self):
        """Download binary attachment via /attachment/download."""
        url = f'/attachment/download?attachment_id={self.attachment_pdf.id}'
        response = self.url_open(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.content,
            self.binary_data,
            "Downloaded file content must match the binary data stored in attachment."
        )

    def test_08_download_attachment_url(self):
        """Download URL attachment via /attachment/download and check redirection."""
        url = f'/attachment/download?attachment_id={self.attachment_link.id}'
        response = self.url_open(url, allow_redirects=False)
        self.assertIn(
            response.status_code,
            [301, 302, 303],
            "URL attachment download should return a redirect."
        )
        self.assertEqual(
            response.headers.get('Location'),
            self.attachment_link.url,
            "Redirect location should match attachment URL."
        )

    def test_09_download_attachment_url_empty(self):
        """Download URL attachment with empty URL returns 404."""
        url = f'/attachment/download?attachment_id={self.attachment_empty_url.id}'
        response = self.url_open(url)
        self.assertEqual(response.status_code, 404)

    def test_10_download_attachment_non_existent(self):
        """Download non-existent attachment ID redirects to /shop."""
        url = '/attachment/download?attachment_id=9999999'
        response = self.url_open(url, allow_redirects=False)
        self.assertIn(
            response.status_code,
            [301, 302, 303],
            "Non-existent attachment should redirect."
        )
        self.assertEqual(
            response.headers.get('Location'),
            '/shop',
            "Non-existent attachment should redirect to /shop."
        )

    def test_11_download_attachment_invalid_id(self):
        """Download attachment with non-integer ID redirects to /shop."""
        url = '/attachment/download?attachment_id=invalid_text'
        response = self.url_open(url, allow_redirects=False)
        self.assertIn(
            response.status_code,
            [301, 302, 303],
            "Invalid attachment ID format should redirect."
        )
        self.assertEqual(
            response.headers.get('Location'),
            '/shop',
            "Invalid attachment ID format should redirect to /shop."
        )

    def test_12_download_attachment_unpublished_product(self):
        """Attachments of an unpublished product are not downloadable."""
        hidden_product = self.env['product.template'].create({
            'name': 'HTTP Test Unpublished Product',
            'list_price': 10.0,
            'is_published': False,
        })
        hidden_attachment = self.env['ir.attachment'].create({
            'name': 'Hidden.pdf',
            'type': 'binary',
            'raw': VALID_PDF,
            'res_model': 'product.template',
            'res_id': hidden_product.id,
            'access_token': False,
        })
        self.env.flush_all()
        url = f'/attachment/download?attachment_id={hidden_attachment.id}'
        response = self.url_open(url, allow_redirects=False)
        self.assertIn(response.status_code, [301, 302, 303])
        self.assertEqual(response.headers.get('Location'), '/shop')
