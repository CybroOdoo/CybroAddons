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

import json

from odoo.tests import HttpCase, tagged
from odoo.tests.common import new_test_user

from .common import PNG_B64, PNG_DATA_URL, DesignerTestMixin


@tagged('post_install', '-at_install')
class TestDesignerController(DesignerTestMixin, HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._create_designer_data()
        cls.portal_user = new_test_user(
            cls.env, login='designer_portal', groups='base.group_portal')

    # ------------------------------------------------------------------
    # Pages
    # ------------------------------------------------------------------
    def test_categories_page_lists_only_categories_with_designable_products(self):
        response = self.url_open('/shop/designer')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Test Mugs', response.text)
        self.assertNotIn('Test Empty Category', response.text)

    def test_category_page_lists_designable_products(self):
        response = self.url_open('/shop/designer/category/%s' % self.category.id)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Test Designable Mug', response.text)

    def test_unknown_category_redirects_to_categories(self):
        response = self.url_open('/shop/designer/category/999999', allow_redirects=False)
        self.assertIn(response.status_code, (301, 302, 303))
        self.assertTrue(response.headers['Location'].endswith('/shop/designer'))

    def test_designer_page_for_designable_product(self):
        response = self.url_open('/shop/designer/%s' % self.product.id)
        self.assertEqual(response.status_code, 200)

    def test_designer_page_redirects_for_non_designable_product(self):
        response = self.url_open(
            '/shop/designer/%s' % self.plain_product.id, allow_redirects=False)
        self.assertIn(response.status_code, (301, 302, 303))
        self.assertTrue(response.headers['Location'].endswith('/shop'))

    # ------------------------------------------------------------------
    # save / load design
    # ------------------------------------------------------------------
    def test_save_design_creates_lines_and_skips_helpers(self):
        self.authenticate(None, None)
        result = self._jsonrpc('/shop/designer/save', {
            'product_id': self.product.id,
            'design_data': self._design_payload(),
            'quantity': 6,
            'variant_id': self.variant.id,
            'preview_image': PNG_DATA_URL,
        })
        self.assertTrue(result['success'])
        customization = self.env['product.design.customization'].browse(result['customization_id'])
        self.assertEqual(customization.state, 'saved')
        self.assertEqual(customization.quantity, 6)
        self.assertEqual(customization.product_id, self.variant)
        self.assertTrue(customization.preview_image)
        lines = customization.customization_line_ids
        # Guide and placeholder objects are skipped: one text + one image.
        self.assertEqual(len(lines), 2)
        text_line = lines.filtered('custom_text')
        self.assertEqual(text_line.custom_text, 'Hello')
        self.assertEqual(text_line.font_family, 'TestFontA')
        self.assertEqual(text_line.font_size, 24)
        self.assertEqual(text_line.font_color, '#FF0000')
        self.assertEqual(text_line.text_alignment, 'left')
        self.assertTrue(text_line.is_bold)
        self.assertTrue(text_line.is_italic)
        self.assertTrue(text_line.is_underline)
        self.assertEqual(text_line.custom_width, 200)
        self.assertTrue(lines.filtered('custom_image'))

    def test_save_design_accepts_json_string_and_front_back_structure(self):
        self.authenticate(None, None)
        payload = {
            'front': self._design_payload('Front', with_image=False),
            'back': self._design_payload('Back', with_image=False),
        }
        result = self._jsonrpc('/shop/designer/save', {
            'product_id': self.product.id,
            'design_data': json.dumps(payload),
        })
        customization = self.env['product.design.customization'].browse(result['customization_id'])
        self.assertEqual(
            sorted(customization.customization_line_ids.mapped('custom_text')),
            ['Back', 'Front'])

    def test_save_design_upserts_existing_draft(self):
        self.authenticate(None, None)
        first = self._jsonrpc('/shop/designer/save', {
            'product_id': self.product.id,
            'design_data': self._design_payload('One', with_image=False),
        })
        second = self._jsonrpc('/shop/designer/save', {
            'product_id': self.product.id,
            'design_data': self._design_payload('Two', with_image=False),
            'customization_id': first['customization_id'],
        })
        self.assertEqual(first['customization_id'], second['customization_id'])
        customization = self.env['product.design.customization'].browse(second['customization_id'])
        self.assertEqual(customization.customization_line_ids.mapped('custom_text'), ['Two'])

    def test_save_design_unknown_product(self):
        self.authenticate(None, None)
        result = self._jsonrpc('/shop/designer/save', {
            'product_id': 999999,
            'design_data': {'objects': []},
        })
        self.assertEqual(result, {'error': 'Product not found'})

    def test_save_design_ignores_variant_of_other_template(self):
        other_variant = self.plain_product.product_variant_id
        self.authenticate(None, None)
        result = self._jsonrpc('/shop/designer/save', {
            'product_id': self.product.id,
            'design_data': {'objects': []},
            'variant_id': other_variant.id,
        })
        customization = self.env['product.design.customization'].browse(result['customization_id'])
        self.assertFalse(customization.product_id)

    def test_load_saved_design(self):
        self.authenticate('admin', 'admin')
        params = {'product_id': self.product.id, 'variant_id': self.variant.id}
        self.assertEqual(self._jsonrpc('/shop/designer/load_saved', params), {})
        saved = self._jsonrpc('/shop/designer/save', {
            'product_id': self.product.id,
            'design_data': self._design_payload('Saved', with_image=False),
            'quantity': 3,
            'variant_id': self.variant.id,
        })
        loaded = self._jsonrpc('/shop/designer/load_saved', params)
        self.assertEqual(loaded['customization_id'], saved['customization_id'])
        self.assertEqual(loaded['variant_id'], self.variant.id)
        self.assertEqual(loaded['quantity'], 3)
        self.assertIn('Saved', loaded['design_json'])

    # ------------------------------------------------------------------
    # upload image
    # ------------------------------------------------------------------
    def test_upload_image_requires_data(self):
        self.authenticate(None, None)
        result = self._jsonrpc('/shop/designer/upload_image', {'image_data': ''})
        self.assertEqual(result, {'error': 'No image data provided'})

    def test_upload_image_success(self):
        self.authenticate(None, None)
        result = self._jsonrpc('/shop/designer/upload_image', {'image_data': PNG_DATA_URL})
        self.assertTrue(result['success'])
        self.assertEqual(result['image_data'], PNG_DATA_URL)

    def test_upload_image_too_large(self):
        self.env['ir.config_parameter'].sudo().set_str(
            'website_product_customizer.max_upload_size', '0')
        self.authenticate(None, None)
        result = self._jsonrpc('/shop/designer/upload_image', {'image_data': PNG_B64})
        self.assertIn('Image too large', result['error'])

    # ------------------------------------------------------------------
    # templates
    # ------------------------------------------------------------------
    def test_get_templates_filters_by_product_and_active(self):
        Template = self.env['product.design.template']
        active = Template.create({'name': 'Active T', 'product_tmpl_id': self.product.id,
                                  'design_data': '{"objects": []}'})
        Template.create({'name': 'Archived T', 'product_tmpl_id': self.product.id,
                         'active': False})
        Template.create({'name': 'Other product T', 'product_tmpl_id': self.plain_product.id})
        self.authenticate(None, None)
        result = self._jsonrpc('/shop/designer/get_templates', {'product_id': self.product.id})
        self.assertEqual([t['id'] for t in result], [active.id])
        self.assertEqual(result[0]['name'], 'Active T')

    def test_get_templates_filters_by_category(self):
        template = self.env['product.design.template'].create({
            'name': 'Category T', 'design_category_id': self.category.id})
        self.authenticate(None, None)
        result = self._jsonrpc('/shop/designer/get_templates', {'category_id': self.category.id})
        self.assertIn(template.id, [t['id'] for t in result])

    def test_save_as_template_internal_user(self):
        self.authenticate('admin', 'admin')
        result = self._jsonrpc('/shop/designer/save_as_template', {
            'product_id': self.product.id,
            'design_data': {'objects': []},
            'preview_image': PNG_DATA_URL,
        })
        self.assertTrue(result['success'])
        template = self.env['product.design.template'].browse(result['template_id'])
        self.assertEqual(template.product_tmpl_id, self.product)
        self.assertEqual(template.design_category_id, self.category)
        self.assertTrue(template.preview_image)
        self.assertEqual(result['template_name'], 'Test Designable Mug — Template')

    def test_save_as_template_rejects_portal_user(self):
        self.authenticate('designer_portal', 'designer_portal')
        result = self._jsonrpc('/shop/designer/save_as_template', {
            'product_id': self.product.id,
            'design_data': {'objects': []},
        })
        self.assertIn('Unauthorized', result['error'])

    def test_update_template(self):
        template = self.env['product.design.template'].create({
            'name': 'Old name', 'product_tmpl_id': self.product.id})
        self.authenticate('admin', 'admin')
        result = self._jsonrpc('/shop/designer/update_template', {
            'template_id': template.id,
            'design_data': {'objects': [{'type': 'i-text', 'text': 'x'}]},
            'template_name': 'New name',
            'preview_image_back': PNG_DATA_URL,
        })
        self.assertTrue(result['success'])
        self.assertEqual(template.name, 'New name')
        self.assertIn('i-text', template.design_data)
        self.assertTrue(template.preview_image_back)

    def test_update_template_not_found_and_unauthorized(self):
        self.authenticate('admin', 'admin')
        result = self._jsonrpc('/shop/designer/update_template', {
            'template_id': 999999, 'design_data': '{}'})
        self.assertEqual(result, {'error': 'Template not found'})
        self.authenticate('designer_portal', 'designer_portal')
        result = self._jsonrpc('/shop/designer/update_template', {
            'template_id': 1, 'design_data': '{}'})
        self.assertIn('Unauthorized', result['error'])

    # ------------------------------------------------------------------
    # design area configuration
    # ------------------------------------------------------------------
    def test_save_area_config_template_front_and_back(self):
        self.authenticate('admin', 'admin')
        config = {'left': 5, 'top': 6, 'width': 70, 'height': 80}
        self.assertTrue(self._jsonrpc('/shop/designer/save_area_config', {
            'product_id': self.product.id, 'config_data': config})['success'])
        self.assertTrue(self._jsonrpc('/shop/designer/save_area_config', {
            'product_id': self.product.id, 'config_data': config, 'side': 'back'})['success'])
        self.assertEqual(
            (self.product.design_area_left, self.product.design_area_top,
             self.product.design_area_width, self.product.design_area_height),
            (5, 6, 70, 80))
        self.assertEqual(
            (self.product.design_area_back_left, self.product.design_area_back_width), (5, 70))

    def test_save_area_config_variant_override(self):
        self.variant.design_variant_override = True
        self.authenticate('admin', 'admin')
        result = self._jsonrpc('/shop/designer/save_area_config', {
            'product_id': self.product.id,
            'config_data': {'left': 1, 'top': 2, 'width': 30, 'height': 40},
            'variant_id': self.variant.id,
        })
        self.assertTrue(result['success'])
        self.assertEqual(self.variant.variant_design_area_width, 30)
        self.assertEqual(self.product.design_area_width, 100)  # template untouched

    def test_save_area_config_rejects_portal_user(self):
        self.authenticate('designer_portal', 'designer_portal')
        result = self._jsonrpc('/shop/designer/save_area_config', {
            'product_id': self.product.id, 'config_data': {'left': 1}})
        self.assertEqual(result, {'error': 'Unauthorized'})

    # ------------------------------------------------------------------
    # variant info
    # ------------------------------------------------------------------
    def test_get_variant_info(self):
        self.authenticate(None, None)
        result = self._jsonrpc('/shop/designer/get_variant_info', {
            'product_id': self.product.id, 'variant_id': self.variant.id})
        self.assertTrue(result['success'])
        self.assertEqual(result['variant_id'], self.variant.id)
        self.assertEqual(result['design_max_characters'], 40)
        self.assertEqual(result['min_order_quantity'], 5)
        self.assertEqual([f['id'] for f in result['fonts']], [self.font_a.id])
        self.assertEqual([c['color_code'] for c in result['bg_colors']], ['#FF0000'])
        self.assertEqual([c['color_code'] for c in result['text_colors']], ['#0000FF'])
        # No design base image -> falls back to the main product image.
        self.assertTrue(result['front_image_url'].endswith('/image_1920'))
        self.assertEqual(result['back_image_url'], '')

    def test_get_variant_info_invalid(self):
        self.authenticate(None, None)
        result = self._jsonrpc('/shop/designer/get_variant_info', {
            'product_id': self.product.id,
            'variant_id': self.plain_product.product_variant_id.id})
        self.assertEqual(result, {'error': 'Invalid variant'})
        result = self._jsonrpc('/shop/designer/get_variant_info', {
            'product_id': 999999, 'variant_id': 1})
        self.assertEqual(result, {'error': 'Product not found'})

    # ------------------------------------------------------------------
    # add to cart
    # ------------------------------------------------------------------
    def test_add_to_cart_errors(self):
        self.authenticate(None, None)
        result = self._jsonrpc('/shop/designer/add_to_cart', {
            'product_id': 999999, 'customization_id': 1})
        self.assertEqual(result, {'error': 'Product not found'})
        result = self._jsonrpc('/shop/designer/add_to_cart', {
            'product_id': self.product.id, 'customization_id': 999999})
        self.assertEqual(result, {'error': 'Design not found'})

    def test_add_to_cart_keeps_each_design_on_its_own_line(self):
        self.authenticate(None, None)
        customizations = []
        for text in ('First', 'Second'):
            saved = self._jsonrpc('/shop/designer/save', {
                'product_id': self.product.id,
                'design_data': self._design_payload(text, with_image=False),
            })
            customizations.append(
                self.env['product.design.customization'].browse(saved['customization_id']))
            # Adding to cart marks the design as ordered, so the next save
            # creates a new record instead of updating this one.
            result = self._jsonrpc('/shop/designer/add_to_cart', {
                'product_id': self.product.id,
                'customization_id': saved['customization_id'],
                'variant_id': self.variant.id,
                'quantity': 5,
                'preview_image': PNG_DATA_URL,
            })
            self.assertTrue(result['success'])
        first, second = customizations
        self.assertEqual(first.state, 'ordered')
        self.assertEqual(second.state, 'ordered')
        self.assertNotEqual(first.sale_order_line_id, second.sale_order_line_id)
        self.assertEqual(first.sale_order_line_id.order_id, second.sale_order_line_id.order_id)
        self.assertIn('Custom Text: First', first.sale_order_line_id.name)
        self.assertEqual(first.sale_order_line_id.design_customization_id, first)
