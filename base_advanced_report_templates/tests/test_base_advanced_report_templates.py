# -*- coding: utf-8 -*-
################################################################################
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
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
# pylint: disable=protected-access,import-error,no-name-in-module
"""Unit test suite for base_advanced_report_templates module."""
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, tagged
from odoo.addons.base_advanced_report_templates.wizard import (
    base_document_layout,
)


@tagged('post_install', '-at_install', 'base_advanced_report_templates')
class TestBaseAdvancedReportTemplates(TransactionCase):
    """Test suite for document layouts, themes, and report models."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for companies, layouts, and orders."""
        super().setUpClass()
        cls.company = cls.env.company
        sample_b64 = (
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z'
            '/D/PwAHAwL/qGeMxAAAAABJRU5ErkJggg=='
        )
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Report Partner',
            'image_1920': sample_b64,
            'street': '123 Business St',
            'city': 'Cityville',
            'zip': '12345',
            'vat': 'US123456789',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Report Product',
            'image_1920': sample_b64,
            'image_128': sample_b64,
            'list_price': 100.0,
            'standard_price': 50.0,
        })

        cls.theme_modern = cls.env.ref(
            'base_advanced_report_templates.modern'
        )
        cls.theme_standard = cls.env.ref(
            'base_advanced_report_templates.standard'
        )
        cls.theme_traditional = cls.env.ref(
            'base_advanced_report_templates.traditional'
        )
        cls.theme_attractive = cls.env.ref(
            'base_advanced_report_templates.attractive'
        )

        cls.company.write({
            'sale_document_layout_id': cls.theme_modern.id,
            'purchase_document_layout_id': cls.theme_standard.id,
            'account_document_layout_id': cls.theme_traditional.id,
            'stock_document_layout_id': cls.theme_attractive.id,
        })
        if hasattr(cls.company, 'document_layout_id'):
            cls.company.document_layout_id = cls.theme_traditional.id

    def test_doc_layout_crud(self):
        """Verify doc.layout creation, defaults, and field updates."""
        custom_layout = self.env['doc.layout'].create({
            'name': 'Custom Purple',
            'theme_style': 'modern',
            'base_color': '#5a2d82',
            'heading_text_color': '#ffffff',
            'text_color': '#333333',
            'customer_text_color': '#111111',
            'company_text_color': '#777777',
            'logo_position': 'left',
            'customer_position': 'right',
            'company_position': 'left',
        })
        self.assertEqual(custom_layout.name, 'Custom Purple')
        self.assertEqual(custom_layout.theme_style, 'modern')
        self.assertEqual(custom_layout.base_color, '#5a2d82')
        self.assertEqual(custom_layout.heading_text_color, '#ffffff')
        self.assertEqual(custom_layout.text_color, '#333333')
        self.assertEqual(custom_layout.customer_text_color, '#111111')
        self.assertEqual(custom_layout.company_text_color, '#777777')
        self.assertEqual(custom_layout.logo_position, 'left')
        self.assertEqual(custom_layout.customer_position, 'right')
        self.assertEqual(custom_layout.company_position, 'left')
        if hasattr(custom_layout, 'company_id'):
            self.assertEqual(custom_layout.company_id, self.env.company)

        # Verify predefined xml layout records exist and have theme_style set
        self.assertTrue(self.theme_modern)
        self.assertEqual(self.theme_modern.theme_style, 'modern')
        self.assertTrue(self.theme_standard)
        self.assertEqual(self.theme_standard.theme_style, 'standard')
        self.assertTrue(self.theme_traditional)
        self.assertEqual(self.theme_traditional.theme_style, 'traditional')
        self.assertTrue(self.theme_attractive)
        self.assertEqual(self.theme_attractive.theme_style, 'attractive')

    def test_doc_layout_security(self):
        """Verify doc.layout read-only access for users and CRUD restriction."""
        regular_user = self.env['res.users'].create({
            'name': 'Report Internal User',
            'login': 'report_internal_user_test',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        layout_as_user = self.env['doc.layout'].with_user(regular_user)
        # Internal users can read layout records
        layouts = layout_as_user.search([])
        self.assertTrue(len(layouts) > 0)

        # Internal users cannot create new layouts
        with self.assertRaises(AccessError):
            layout_as_user.create({'name': 'Disallowed Layout'})

        # Internal users cannot write existing layouts
        with self.assertRaises(AccessError):
            self.theme_traditional.with_user(regular_user).write(
                {'base_color': '#000000'}
            )

        # Internal users cannot unlink layouts
        with self.assertRaises(AccessError):
            self.theme_traditional.with_user(regular_user).unlink()

    def test_res_company_layout_fields(self):
        """Verify res.company layout configuration fields."""
        self.assertEqual(
            self.company.sale_document_layout_id, self.theme_modern
        )
        self.assertEqual(
            self.company.purchase_document_layout_id, self.theme_standard
        )
        self.assertEqual(
            self.company.account_document_layout_id, self.theme_traditional
        )
        self.assertEqual(
            self.company.stock_document_layout_id, self.theme_attractive
        )

    def test_sale_order_and_line_fields(self):
        """Verify customer image and theme on sale order and line."""
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 2.0,
                'price_unit': 100.0,
            })],
        })
        self.assertEqual(sale_order.theme_id, self.theme_modern)
        self.assertTrue(sale_order.customer_image)
        line = sale_order.order_line[0]
        self.assertTrue(line.order_line_image)

    def test_purchase_order_and_line_fields(self):
        """Verify theme and line image on purchase order and line."""
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_qty': 5.0,
                'price_unit': 50.0,
            })],
        })
        self.assertEqual(purchase_order.theme_id, self.theme_standard)
        line = purchase_order.order_line[0]
        self.assertTrue(line.order_line_image)

    def test_account_move_and_line_fields(self):
        """Verify theme and line image on invoice and line."""
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1.0,
                'price_unit': 120.0,
            })],
        })
        self.assertEqual(invoice.theme_id, self.theme_traditional)
        line = invoice.invoice_line_ids[0]
        self.assertTrue(line.order_line_image)

    def test_stock_picking_and_move_fields(self):
        """Verify theme and line image on stock picking and move."""
        warehouse = self.env['stock.warehouse'].search([
            ('company_id', '=', self.company.id),
        ], limit=1)
        picking_type = warehouse.out_type_id
        customer_loc = self.env.ref('stock.stock_location_customers')
        picking = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'picking_type_id': picking_type.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': customer_loc.id,
            'move_ids': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 3.0,
                'location_id': picking_type.default_location_src_id.id,
                'location_dest_id': customer_loc.id,
            })],
        })
        self.assertEqual(picking.theme_id, self.theme_attractive)
        move = picking.move_ids[0]
        self.assertTrue(move.order_line_image)

    def test_report_rendering_all_themes_and_models(self):
        """Verify report HTML rendering for all 4 models across all 4 themes."""
        themes = [
            self.theme_traditional,
            self.theme_standard,
            self.theme_modern,
            self.theme_attractive,
        ]

        # 1. Sale Order
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
            })],
        })
        so_theme_markers = {
            self.theme_traditional.id: 'Customer Address',
            self.theme_standard.id: 'Quotation #',
            self.theme_modern.id: 'Quotation Date:',
            self.theme_attractive.id: 'Invoicing and shipping Address',
        }
        for theme in themes:
            sale_order.theme_id = theme
            html, _ = self.env['ir.actions.report']._render_qweb_html(
                'base_advanced_report_templates.report_saleorder_custom',
                [sale_order.id],
            )
            self.assertTrue(html)
            self.assertIn(theme.base_color, str(html))
            self.assertIn(so_theme_markers[theme.id], str(html))

        # 2. Purchase Order
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_qty': 2.0,
                'price_unit': 45.0,
            })],
        })
        po_theme_markers = {
            self.theme_traditional.id: 'Purchase Representative',
            self.theme_standard.id: 'Request for Quotation #',
            self.theme_modern.id: 'Vendor',
            self.theme_attractive.id: 'Order Date:',
        }
        for theme in themes:
            purchase_order.theme_id = theme
            html, _ = self.env['ir.actions.report']._render_qweb_html(
                'base_advanced_report_templates.report_purchase_custom',
                [purchase_order.id],
            )
            self.assertTrue(html)
            self.assertIn(theme.base_color, str(html))
            self.assertIn(po_theme_markers[theme.id], str(html))

        # 3. Account Move (Invoice)
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1.0,
                'price_unit': 150.0,
            })],
        })
        for theme in themes:
            invoice.theme_id = theme
            html, _ = self.env['ir.actions.report']._render_qweb_html(
                'base_advanced_report_templates.report_invoice_custom',
                [invoice.id],
            )
            self.assertTrue(html)
            self.assertIn(theme.base_color, str(html))

        # 4. Stock Picking
        warehouse = self.env['stock.warehouse'].search([
            ('company_id', '=', self.company.id),
        ], limit=1)
        picking_type = warehouse.out_type_id
        customer_loc = self.env.ref('stock.stock_location_customers')
        picking = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'picking_type_id': picking_type.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': customer_loc.id,
            'move_ids': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
                'location_id': picking_type.default_location_src_id.id,
                'location_dest_id': customer_loc.id,
            })],
        })
        for theme in themes:
            picking.theme_id = theme
            html, _ = self.env['ir.actions.report']._render_qweb_html(
                'base_advanced_report_templates.report_deliveryslip_custom',
                [picking.id],
            )
            self.assertTrue(html)
            self.assertIn(theme.base_color, str(html))

    def test_standard_theme_text_colors_applied(self):
        """Verify standard theme customer and company text colors are applied."""
        self.theme_standard.write({
            'customer_text_color': '#336699',
            'company_text_color': '#663399',
        })

        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 80.0,
            })],
        })
        sale_order.theme_id = self.theme_standard
        html_so, _ = self.env['ir.actions.report']._render_qweb_html(
            'base_advanced_report_templates.report_saleorder_custom',
            [sale_order.id],
        )
        self.assertIn('#336699', str(html_so))
        self.assertIn('#663399', str(html_so))

        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_qty': 1.0,
                'price_unit': 40.0,
            })],
        })
        purchase_order.theme_id = self.theme_standard
        html_po, _ = self.env['ir.actions.report']._render_qweb_html(
            'base_advanced_report_templates.report_purchase_custom',
            [purchase_order.id],
        )
        self.assertIn('#336699', str(html_po))
        self.assertIn('#663399', str(html_po))

    def test_custom_theme_fallback(self):
        """Verify custom or renamed themes do not fall back to default report."""
        custom_theme_modern = self.env['doc.layout'].create({
            'name': 'Custom Emerald',
            'theme_style': 'modern',
            'base_color': '#2ecc71',
            'heading_text_color': '#ffffff',
            'customer_text_color': '#112233',
            'company_text_color': '#445566',
        })
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
            })],
        })
        sale_order.theme_id = custom_theme_modern
        html, _ = self.env['ir.actions.report']._render_qweb_html(
            'base_advanced_report_templates.report_saleorder_custom',
            [sale_order.id],
        )
        self.assertIn('#2ecc71', str(html))
        self.assertIn('#112233', str(html))
        self.assertIn('Quotation Date:', str(html))

        # Test custom theme without style defaulting gracefully to traditional
        custom_theme_default = self.env['doc.layout'].create({
            'name': 'Bespoke Dark',
            'theme_style': 'traditional',
            'base_color': '#111111',
            'heading_text_color': '#ffffff',
        })
        sale_order.theme_id = custom_theme_default
        html_def, _ = self.env['ir.actions.report']._render_qweb_html(
            'base_advanced_report_templates.report_saleorder_custom',
            [sale_order.id],
        )
        self.assertIn('#111111', str(html_def))
        self.assertIn('Customer Address', str(html_def))

        # Test sale order without any theme falls back to standard sale report
        sale_order.theme_id = False
        html_base, _ = self.env['ir.actions.report']._render_qweb_html(
            'base_advanced_report_templates.report_saleorder_custom',
            [sale_order.id],
        )
        self.assertTrue(html_base)

    def test_base_document_layout_wizard_preview(self):
        """Verify base.document.layout wizard preview rendering."""
        report_layout = self.env['report.layout'].search([], limit=1)
        wizard = self.env['base.document.layout'].create({
            'company_id': self.company.id,
            'report_layout_id': report_layout.id,
            'sale_document_layout_id': self.theme_modern.id,
            'purchase_document_layout_id': self.theme_standard.id,
            'account_document_layout_id': self.theme_traditional.id,
            'stock_document_layout_id': self.theme_attractive.id,
            'watermark': True,
            'watermark_show': 'logo',
        })
        self.assertTrue(wizard.watermark)
        self.assertEqual(wizard.watermark_show, 'logo')

        # Trigger compute_preview for all themes
        themes = [
            self.theme_modern,
            self.theme_standard,
            self.theme_traditional,
            self.theme_attractive,
        ]
        for theme in themes:
            wizard.write({
                'sale_document_layout_id': theme.id,
                'purchase_document_layout_id': theme.id,
                'account_document_layout_id': theme.id,
                'stock_document_layout_id': theme.id,
            })
            base_document_layout.BaseDocumentLayout._compute_preview(wizard)
            self.assertTrue(wizard.preview)
            self.assertIn(theme.base_color, str(wizard.preview))

        # Test active_model context handling
        for model_name in ['sale.order', 'purchase.order', 'account.move', 'stock.picking']:
            ctx_wizard = wizard.with_context(active_model=model_name)
            base_document_layout.BaseDocumentLayout._compute_preview(ctx_wizard)
            self.assertTrue(ctx_wizard.preview)
