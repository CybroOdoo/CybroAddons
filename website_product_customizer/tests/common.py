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

# 1x1 transparent PNG used wherever a valid image payload is required.
PNG_B64 = (
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='
)
PNG_DATA_URL = 'data:image/png;base64,' + PNG_B64


class DesignerTestMixin:
    """Shared fixtures for the Website Product Customizer tests."""

    @classmethod
    def _create_designer_data(cls):
        env = cls.env
        cls.category = env['product.public.category'].create({'name': 'Test Mugs'})
        cls.empty_category = env['product.public.category'].create({'name': 'Test Empty Category'})
        cls.font_a = env['product.design.font'].create({
            'name': 'Test Font A',
            'font_family_name': 'TestFontA',
            'provider': 'system',
        })
        cls.font_b = env['product.design.font'].create({
            'name': 'Test Font B',
            'font_family_name': 'TestFontB',
            'provider': 'google',
            'google_url': 'https://fonts.googleapis.com/css2?family=Roboto&display=swap',
        })
        cls.color_red = env['product.design.color'].create({'name': 'Test Red', 'color_code': '#FF0000'})
        cls.color_blue = env['product.design.color'].create({'name': 'Test Blue', 'color_code': '#0000FF'})
        cls.product = env['product.template'].create({
            'name': 'Test Designable Mug',
            'list_price': 12.0,
            'is_designable': True,
            'is_published': True,
            'design_category_id': cls.category.id,
            'design_font_ids': [(6, 0, cls.font_a.ids)],
            'design_bg_color_ids': [(6, 0, cls.color_red.ids)],
            'design_text_color_ids': [(6, 0, cls.color_blue.ids)],
            'design_max_characters': 40,
            'min_order_quantity': 5,
            'production_time_days': 4,
        })
        cls.variant = cls.product.product_variant_id
        cls.plain_product = env['product.template'].create({
            'name': 'Test Plain Product',
            'is_designable': False,
            'is_published': True,
        })

    @staticmethod
    def _design_payload(text='Hello', with_image=True):
        """Return a Fabric.js style payload with a text, an image and a guide."""
        objects = [
            {'type': 'i-text', 'text': text, 'fontFamily': 'TestFontA', 'fontSize': 24,
             'fill': '#FF0000', 'textAlign': 'left', 'fontWeight': 'bold',
             'fontStyle': 'italic', 'underline': True, 'left': 10, 'top': 20,
             'width': 100, 'height': 30, 'scaleX': 2, 'scaleY': 1, 'angle': 5},
            {'type': 'rect', 'isGuide': True},
            {'type': 'i-text', 'text': 'placeholder', 'isPlaceholder': True},
        ]
        if with_image:
            objects.append({'type': 'image', 'src': PNG_DATA_URL, 'left': 1, 'top': 2,
                            'width': 10, 'height': 10, 'scaleX': 1, 'scaleY': 1, 'angle': 0})
        return {'objects': objects}

    def _jsonrpc(self, route, params):
        return self.make_jsonrpc_request(route, params)
