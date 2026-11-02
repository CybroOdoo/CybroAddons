# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#############################################################################
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools.safe_eval import safe_eval

# 1x1 pixel PNG in base64 string
SAMPLE_IMAGE = (
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwAD'
    'hgGAWjR9awAAAABJRU5ErkJggg=='
)


@tagged('post_install', '-at_install')
class TestSaleOrderLineViews(TransactionCase):
    """Test suite for odoo_sale_order_line_views module covering sale.order.line
    related fields, quotation and sale order line actions, menus, and views.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

        # Customer with email and phone
        cls.partner_customer = cls.env['res.partner'].create({
            'name': 'Test Customer With Contact Info',
            'email': 'customer.test@example.com',
            'phone': '+1 555-0199',
            'company_id': cls.company.id,
        })

        # Customer without email and phone
        cls.partner_empty = cls.env['res.partner'].create({
            'name': 'Test Customer Without Contact Info',
            'email': False,
            'phone': False,
            'company_id': cls.company.id,
        })

        # Product with image
        cls.product_with_image = cls.env['product.product'].create({
            'name': 'Test Product With Image',
            'image_1920': SAMPLE_IMAGE,
            'list_price': 100.0,
        })

        # Product without image
        cls.product_without_image = cls.env['product.product'].create({
            'name': 'Test Product Without Image',
            'image_1920': False,
            'list_price': 50.0,
        })

        # Draft Quotation
        cls.quotation = cls.env['sale.order'].create({
            'partner_id': cls.partner_customer.id,
            'order_line': [
                (0, 0, {
                    'product_id': cls.product_with_image.id,
                    'product_uom_qty': 2.0,
                    'price_unit': 100.0,
                }),
                (0, 0, {
                    'product_id': cls.product_without_image.id,
                    'product_uom_qty': 1.0,
                    'price_unit': 50.0,
                }),
            ],
        })

        # Confirmed Sale Order
        cls.confirmed_sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner_customer.id,
            'order_line': [
                (0, 0, {
                    'product_id': cls.product_with_image.id,
                    'product_uom_qty': 5.0,
                    'price_unit': 100.0,
                }),
            ],
        })
        cls.confirmed_sale_order.action_confirm()

    def test_order_line_image_related_field(self):
        """Test that order_line_image is properly related to product image."""
        line_with_img = self.quotation.order_line.filtered(
            lambda l: l.product_id == self.product_with_image
        )
        line_without_img = self.quotation.order_line.filtered(
            lambda l: l.product_id == self.product_without_image
        )

        self.assertTrue(line_with_img, "Line with product image should exist.")
        self.assertTrue(line_with_img.order_line_image)
        self.assertEqual(
            line_with_img.order_line_image,
            self.product_with_image.image_1920,
            "order_line_image should match product image_1920."
        )

        self.assertTrue(line_without_img, "Line without product image should exist.")
        self.assertFalse(
            line_without_img.order_line_image,
            "order_line_image should be False when product has no image."
        )

    def test_order_line_image_update_on_product_image_change(self):
        """Test that modifying the product image propagates to order_line_image."""
        line = self.quotation.order_line.filtered(
            lambda l: l.product_id == self.product_without_image
        )
        self.assertFalse(line.order_line_image)

        # Update product image
        self.product_without_image.write({'image_1920': SAMPLE_IMAGE})
        self.assertTrue(line.order_line_image)
        self.assertEqual(
            line.order_line_image,
            self.product_without_image.image_1920,
            "order_line_image should reflect updated product image."
        )

        # Clear image back
        self.product_without_image.write({'image_1920': False})
        self.assertFalse(
            line.order_line_image,
            "order_line_image should be False after removing product image."
        )

    def test_contact_email_and_phone_related_fields(self):
        """Test that contact_email and contact_phone are related to order_partner_id."""
        line = self.quotation.order_line[0]
        self.assertEqual(
            line.contact_email,
            self.partner_customer.email,
            "contact_email should match partner email."
        )
        self.assertEqual(
            line.contact_phone,
            self.partner_customer.phone,
            "contact_phone should match partner phone."
        )

    def test_contact_email_and_phone_empty_partner(self):
        """Test contact_email and contact_phone when partner has no contact details."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner_empty.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_without_image.id,
                    'product_uom_qty': 1.0,
                }),
            ],
        })
        line = order.order_line[0]
        self.assertFalse(
            line.contact_email,
            "contact_email should be False when partner has no email."
        )
        self.assertFalse(
            line.contact_phone,
            "contact_phone should be False when partner has no phone."
        )

    def test_contact_info_update_propagation(self):
        """Test that updating partner email or phone updates contact_email and contact_phone."""
        partner = self.env['res.partner'].create({
            'name': 'Dynamic Partner',
            'email': 'initial@example.com',
            'phone': '111111',
        })
        order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_with_image.id,
                    'product_uom_qty': 1.0,
                }),
            ],
        })
        line = order.order_line[0]
        self.assertEqual(line.contact_email, 'initial@example.com')
        self.assertEqual(line.contact_phone, '111111')

        partner.write({
            'email': 'updated@example.com',
            'phone': '999999',
        })
        self.assertEqual(line.contact_email, 'updated@example.com')
        self.assertEqual(line.contact_phone, '999999')

    def test_sale_order_line_read_and_search(self):
        """Test reading and searching custom fields on sale.order.line."""
        lines = self.env['sale.order.line'].search([
            ('contact_email', '=', self.partner_customer.email)
        ])
        self.assertTrue(
            self.quotation.order_line[0] in lines,
            "Search by contact_email should find the matching order lines."
        )

        phones = self.env['sale.order.line'].search([
            ('contact_phone', '=', self.partner_customer.phone)
        ])
        self.assertTrue(
            self.quotation.order_line[0] in phones,
            "Search by contact_phone should find the matching order lines."
        )

        read_data = self.quotation.order_line[0].read([
            'order_line_image',
            'contact_email',
            'contact_phone',
        ])
        self.assertTrue(read_data, "Read should return field values.")
        self.assertEqual(read_data[0]['contact_email'], self.partner_customer.email)
        self.assertEqual(read_data[0]['contact_phone'], self.partner_customer.phone)

    def test_quotation_line_views_action(self):
        """Test the quotation line views window action and its domain filtering."""
        action = self.env.ref('odoo_sale_order_line_views.quotation_line_views_action')
        self.assertTrue(action.exists(), "Quotation lines action should exist.")
        self.assertEqual(action.res_model, 'sale.order.line')
        self.assertEqual(action.view_mode, 'list,kanban,form,pivot,graph,calendar')

        # Domain: [('state', 'in', ('draft', 'sent', 'cancel'))]
        domain = safe_eval(action.domain) if isinstance(action.domain, str) else action.domain
        quotation_lines = self.env['sale.order.line'].search(domain)

        # Quotation lines in draft state should match
        for line in self.quotation.order_line:
            self.assertIn(
                line, quotation_lines,
                "Draft quotation line should match quotation line domain."
            )

        # Confirmed sale order lines should NOT match
        for line in self.confirmed_sale_order.order_line:
            self.assertNotIn(
                line, quotation_lines,
                "Confirmed sale order line should NOT match quotation line domain."
            )

        # Action view_ids should include form view mapping
        action_views = {v.view_mode: v.view_id for v in action.view_ids}
        self.assertIn('form', action_views, "view_ids should explicitly include form view.")
        self.assertEqual(
            action_views['form'],
            self.env.ref('odoo_sale_order_line_views.quotation_line_form_view'),
            "Action form view should be quotation_line_form_view."
        )

    def test_sale_order_line_views_action(self):
        """Test the sale order line views window action and its domain filtering."""
        action = self.env.ref('odoo_sale_order_line_views.sale_order_line_views_action')
        self.assertTrue(action.exists(), "Sale order lines action should exist.")
        self.assertEqual(action.res_model, 'sale.order.line')
        self.assertEqual(action.view_mode, 'list,kanban,form,pivot,graph,calendar')

        # Domain: [('state', 'not in', ('draft', 'sent'))]
        domain = safe_eval(action.domain) if isinstance(action.domain, str) else action.domain
        sale_order_lines = self.env['sale.order.line'].search(domain)

        # Confirmed sale order lines should match
        for line in self.confirmed_sale_order.order_line:
            self.assertIn(
                line, sale_order_lines,
                "Confirmed sale order line should match sale order lines action domain."
            )

        # Draft quotation lines should NOT match
        for line in self.quotation.order_line:
            self.assertNotIn(
                line, sale_order_lines,
                "Draft quotation line should NOT match sale order lines action domain."
            )

        # Action view_ids should include form view mapping
        action_views = {v.view_mode: v.view_id for v in action.view_ids}
        self.assertIn('form', action_views, "view_ids should explicitly include form view.")
        self.assertEqual(
            action_views['form'],
            self.env.ref('odoo_sale_order_line_views.sale_order_line_form_view'),
            "Action form view should be sale_order_line_form_view."
        )

    def test_quotation_line_views_rendering(self):
        """Test rendering of all Quotation Line view architectures."""
        view_refs = [
            ('odoo_sale_order_line_views.quotation_line_form_view', 'form'),
            ('odoo_sale_order_line_views.quotation_line_tree_view', 'list'),
            ('odoo_sale_order_line_views.quotation_line_kanban_view', 'kanban'),
            ('odoo_sale_order_line_views.quotation_line_view_pivot', 'pivot'),
            ('odoo_sale_order_line_views.quotation_line_view_graph_view', 'graph'),
            ('odoo_sale_order_line_views.quotation_line_calendar_view', 'calendar'),
        ]

        for xml_id, view_type in view_refs:
            view = self.env.ref(xml_id)
            self.assertTrue(view.exists(), f"View {xml_id} should exist.")
            self.assertTrue(view.active, f"View {xml_id} should be active.")
            self.assertEqual(view.priority, 99, f"View {xml_id} should have priority 99.")

            res = self.env['sale.order.line'].get_view(view.id, view_type)
            self.assertTrue(res.get('arch'), f"Arch should be rendered for {xml_id}.")

    def test_sale_order_line_views_rendering(self):
        """Test rendering of all Sale Order Line view architectures."""
        view_refs = [
            ('odoo_sale_order_line_views.sale_order_line_form_view', 'form'),
            ('odoo_sale_order_line_views.sale_order_line_tree_view', 'list'),
            ('odoo_sale_order_line_views.sale_order_line_kanban_view', 'kanban'),
            ('odoo_sale_order_line_views.sale_order_line_view_pivot', 'pivot'),
            ('odoo_sale_order_line_views.sale_order_line_view_graph_view', 'graph'),
            ('odoo_sale_order_line_views.sale_order_line_calendar_view', 'calendar'),
        ]

        for xml_id, view_type in view_refs:
            view = self.env.ref(xml_id)
            self.assertTrue(view.exists(), f"View {xml_id} should exist.")
            self.assertTrue(view.active, f"View {xml_id} should be active.")
            self.assertEqual(view.priority, 99, f"View {xml_id} should have priority 99.")

            res = self.env['sale.order.line'].get_view(view.id, view_type)
            self.assertTrue(res.get('arch'), f"Arch should be rendered for {xml_id}.")

    def test_menu_items(self):
        """Test that menu items exist and reference correct parent and action."""
        parent_menu = self.env.ref('sale.sale_order_menu')

        quotation_menu = self.env.ref('odoo_sale_order_line_views.menu_quotation_lines')
        self.assertTrue(quotation_menu.exists(), "menu_quotation_lines should exist.")
        self.assertEqual(quotation_menu.parent_id, parent_menu)
        self.assertEqual(
            quotation_menu.action.id,
            self.env.ref('odoo_sale_order_line_views.quotation_line_views_action').id
        )

        order_line_menu = self.env.ref('odoo_sale_order_line_views.menu_sale_order_lines')
        self.assertTrue(order_line_menu.exists(), "menu_sale_order_lines should exist.")
        self.assertEqual(order_line_menu.parent_id, parent_menu)
        self.assertEqual(
            order_line_menu.action.id,
            self.env.ref('odoo_sale_order_line_views.sale_order_line_views_action').id
        )

