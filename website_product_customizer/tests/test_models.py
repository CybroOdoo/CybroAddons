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

from odoo.tests import TransactionCase, tagged

from .common import PNG_B64, DesignerTestMixin


@tagged('post_install', '-at_install')
class TestDesignerModels(DesignerTestMixin, TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._create_designer_data()

    # ------------------------------------------------------------------
    # product.design.customization
    # ------------------------------------------------------------------
    def test_customization_gets_sequence_name(self):
        """A new customization receives a reference from the sequence."""
        customization = self.env['product.design.customization'].create({
            'product_tmpl_id': self.product.id,
        })
        self.assertNotEqual(customization.name, 'New')
        self.assertEqual(customization.state, 'draft')

    def test_customization_explicit_name_is_kept(self):
        customization = self.env['product.design.customization'].create({
            'name': 'MY-DESIGN',
            'product_tmpl_id': self.product.id,
        })
        self.assertEqual(customization.name, 'MY-DESIGN')

    def test_customization_names_are_unique_in_batch(self):
        records = self.env['product.design.customization'].create([
            {'product_tmpl_id': self.product.id},
            {'product_tmpl_id': self.product.id},
        ])
        self.assertEqual(len(set(records.mapped('name'))), 2)

    def test_customization_lines_cascade_on_delete(self):
        customization = self.env['product.design.customization'].create({
            'product_tmpl_id': self.product.id,
            'customization_line_ids': [(0, 0, {'custom_text': 'Hi'})],
        })
        line = customization.customization_line_ids
        customization.unlink()
        self.assertFalse(line.exists())

    # ------------------------------------------------------------------
    # product.design.template
    # ------------------------------------------------------------------
    def test_template_defaults(self):
        template = self.env['product.design.template'].create({
            'name': 'Test Template',
            'product_tmpl_id': self.product.id,
        })
        self.assertEqual(template.template_style, 'modern')
        self.assertEqual(template.usage_count, 0)
        self.assertTrue(template.active)

    def test_product_template_count_and_action(self):
        self.assertEqual(self.product.design_template_count, 0)
        self.env['product.design.template'].create([
            {'name': 'T1', 'product_tmpl_id': self.product.id},
            {'name': 'T2', 'product_tmpl_id': self.product.id},
        ])
        self.assertEqual(self.product.design_template_count, 2)
        action = self.product.action_open_designer_templates()
        self.assertEqual(action['res_model'], 'product.design.template')
        self.assertEqual(action['domain'], [('product_tmpl_id', '=', self.product.id)])
        self.assertEqual(action['context'], {'default_product_tmpl_id': self.product.id})

    # ------------------------------------------------------------------
    # product.design.font
    # ------------------------------------------------------------------
    def test_font_css_url_by_provider(self):
        self.assertFalse(self.font_a.css_url)  # system fonts have no CSS URL
        self.assertEqual(self.font_b.css_url, self.font_b.google_url)

    def test_font_custom_without_file_has_no_css_url(self):
        font = self.env['product.design.font'].create({
            'name': 'Custom Font',
            'font_family_name': 'CustomFont',
            'provider': 'custom',
        })
        self.assertFalse(font.css_url)

    def test_font_custom_with_file_builds_content_url(self):
        font = self.env['product.design.font'].create({
            'name': 'Custom Font 2',
            'font_family_name': 'CustomFont2',
            'provider': 'custom',
            'font_file': PNG_B64,
            'font_filename': 'custom.ttf',
        })
        self.assertIn('/web/content/product.design.font/%s/font_file/custom.ttf' % font.id,
                      font.css_url)

    # ------------------------------------------------------------------
    # product.product design configuration
    # ------------------------------------------------------------------
    def test_variant_config_falls_back_to_template(self):
        config = self.variant._get_design_config()
        self.assertEqual(config['design_max_characters'], 40)
        self.assertEqual(config['min_order_quantity'], 5)
        self.assertEqual(config['production_time_days'], 4)
        self.assertEqual(config['design_font_ids'], self.font_a)
        self.assertEqual(config['design_bg_color_ids'], self.color_red)
        self.assertEqual(config['design_text_color_ids'], self.color_blue)

    def test_variant_config_override(self):
        self.variant.write({
            'design_variant_override': True,
            'variant_design_max_characters': 99,
            'variant_min_order_quantity': 7,
            'variant_design_area_left': 12.5,
            'variant_design_font_ids': [(6, 0, self.font_b.ids)],
            'variant_design_bg_color_ids': [(6, 0, self.color_blue.ids)],
            'variant_design_text_color_ids': [(6, 0, self.color_red.ids)],
        })
        config = self.variant._get_design_config()
        self.assertEqual(config['design_max_characters'], 99)
        self.assertEqual(config['min_order_quantity'], 7)
        self.assertEqual(config['design_area_left'], 12.5)
        self.assertEqual(config['design_font_ids'], self.font_b)
        self.assertEqual(config['design_bg_color_ids'], self.color_blue)
        self.assertEqual(config['design_text_color_ids'], self.color_red)

    def test_variant_design_base_image_fallback(self):
        self.product.design_base_image = PNG_B64
        self.assertTrue(self.variant.design_base_image)
        self.assertFalse(self.variant.design_base_image_variant)
        self.variant.design_base_image_variant = PNG_B64
        self.assertTrue(self.variant.design_base_image_variant)
        self.assertTrue(self.variant.design_base_image)

    def test_variant_design_base_image_back_fallback(self):
        self.assertFalse(self.variant.design_base_image_back)
        self.product.design_base_image_back = PNG_B64
        self.assertTrue(self.variant.design_base_image_back)

    # ------------------------------------------------------------------
    # sale.order / sale.order.line
    # ------------------------------------------------------------------
    def _create_order(self, with_design):
        partner = self.env['res.partner'].create({'name': 'Test Designer Customer'})
        customization = self.env['product.design.customization'].create({
            'product_tmpl_id': self.product.id,
            'partner_id': partner.id,
        })
        order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.variant.id,
                    'product_uom_qty': 1,
                    'design_customization_id': customization.id if with_design else False,
                }),
                (0, 0, {'product_id': self.variant.id, 'product_uom_qty': 2}),
            ],
        })
        return order, customization

    def test_sale_order_with_design(self):
        order, customization = self._create_order(with_design=True)
        self.assertTrue(order.has_design_products)
        self.assertEqual(order.design_customization_count, 1)
        designed = order.order_line.filtered('design_customization_id')
        self.assertTrue(designed.is_designed)
        self.assertFalse((order.order_line - designed).is_designed)
        action = order.action_view_designs()
        self.assertEqual(action['res_model'], 'product.design.customization')
        self.assertEqual(action['domain'], [('id', 'in', [customization.id])])

    def test_sale_order_without_design(self):
        order, _customization = self._create_order(with_design=False)
        self.assertFalse(order.has_design_products)
        self.assertEqual(order.design_customization_count, 0)
        self.assertFalse(any(order.order_line.mapped('is_designed')))

    def test_order_line_is_designed_recomputes(self):
        order, customization = self._create_order(with_design=False)
        line = order.order_line[:1]
        self.assertFalse(line.is_designed)
        line.design_customization_id = customization
        self.assertTrue(line.is_designed)
        self.assertTrue(order.has_design_products)

    # ------------------------------------------------------------------
    # res.config.settings
    # ------------------------------------------------------------------
    def test_max_upload_size_setting_is_stored(self):
        settings = self.env['res.config.settings'].create({'designer_max_upload_size': 25})
        settings.execute()
        value = self.env['ir.config_parameter'].sudo().get_str(
            'website_product_customizer.max_upload_size')
        self.assertEqual(value, '25')
