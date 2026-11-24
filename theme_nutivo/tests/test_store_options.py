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
from odoo.tests import tagged

from odoo.addons.theme_nutivo.controllers.theme_nutivo import NutivoStore
from odoo.addons.theme_nutivo.models.theme_utils import NUTIVO_MEGA_MENU_LIMIT
from odoo.addons.website_sale.tests.common import MockRequest, WebsiteSaleCommon


@tagged('post_install', '-at_install')
class TestNutivoOptions(WebsiteSaleCommon):
    """Test the options, the add-ons, the chips and the Shop mega menu."""

    @classmethod
    def setUpClass(cls):
        """Create a product with a Duration attribute that makes no variant."""
        super().setUpClass()
        cls.env['ir.module.module'].search(
            [('name', '=', 'theme_nutivo')], limit=1)._theme_load(cls.website)
        cls.template = cls.product.product_tmpl_id.sudo()
        cls.attribute = cls.env['product.attribute'].sudo().create({
            'name': 'Nutivo Duration',
            'create_variant': 'no_variant',
            'value_ids': [(0, 0, {'name': '1 year'}), (0, 0, {'name': '2 years'})],
        })
        cls.extra = cls.env['product.template'].sudo().create({
            'name': 'Nutivo Extra Options',
            'is_published': True,
            'list_price': 10.0,
            'attribute_line_ids': [(0, 0, {
                'attribute_id': cls.attribute.id,
                'value_ids': [(6, 0, cls.attribute.value_ids.ids)],
            })],
        })

    def _add_on(self, published=True):
        """Offer a new product as an optional product of the test product."""
        optional = self.env['product.template'].sudo().create({
            'name': 'Nutivo Add-on',
            'is_published': published,
            'list_price': 5.0,
        })
        self.template.sudo().optional_product_ids = optional
        return optional

    def test_needs_options(self):
        """A plain product is added from the card, others need options."""
        self.assertFalse(self.template.sudo()._nutivo_needs_options())
        self.assertTrue(self.extra._nutivo_needs_options())
        self._add_on()
        self.assertTrue(self.template.sudo()._nutivo_needs_options())

    def test_needs_page(self):
        """Only an optional product asking for a custom text needs the page."""
        self.assertFalse(self.extra._nutivo_needs_page())
        self.assertFalse(self.template.sudo()._nutivo_needs_page())
        engraving = self.env['product.attribute'].sudo().create({
            'name': 'Nutivo Engraving',
            'value_ids': [(0, 0, {'name': 'Text', 'is_custom': True})],
        })
        custom = self.env['product.template'].sudo().create({
            'name': 'Nutivo Engraved',
            'is_published': True,
            'attribute_line_ids': [(0, 0, {
                'attribute_id': engraving.id,
                'value_ids': [(6, 0, engraving.value_ids.ids)],
            })],
        })
        self.template.sudo().optional_product_ids = custom
        self.assertTrue(self.template.sudo()._nutivo_needs_page())

    def test_extra_options(self):
        """The attributes that make no variant are given with their values."""
        options = self.extra._nutivo_extra_options()
        self.assertEqual(len(options), 1)
        self.assertEqual(options[0]['name'], 'Nutivo Duration')
        self.assertEqual(
            [value['name'] for value in options[0]['values']],
            ['1 year', '2 years'])
        self.assertFalse(self.template.sudo()._nutivo_extra_options())

    def test_addons(self):
        """Only the published optional products are offered."""
        with MockRequest(self.env, website=self.website) as request:
            template = request.env['product.template'].browse(
                self.template.id)
            self.assertFalse(template._nutivo_addons())
            optional = self._add_on()
            addons = template._nutivo_addons()
            self.assertEqual([a['product'].id for a in addons], optional.ids)
            optional.is_published = False
            self.assertFalse(template._nutivo_addons())

    def test_categories_limit(self):
        """The categories stop at the limit."""
        for index in range(3):
            category = self.env['product.public.category'].sudo().create(
                {'name': 'Nutivo Limit %s' % index})
            self.env['product.template'].sudo().create({
                'name': 'Nutivo Limit Product %s' % index,
                'is_published': True,
                'public_categ_ids': [(6, 0, category.ids)],
            })
        self.assertEqual(len(self.website._nutivo_categories(limit=2)), 2)
        self.assertGreater(len(self.website._nutivo_categories()), 2)

    def test_mega_menu_limit(self):
        """The Shop mega menu lists a few categories and the feature card."""
        for index in range(NUTIVO_MEGA_MENU_LIMIT + 2):
            category = self.env['product.public.category'].sudo().create(
                {'name': 'Nutivo Mega %s' % index})
            self.env['product.template'].sudo().create({
                'name': 'Nutivo Mega Product %s' % index,
                'is_published': True,
                'public_categ_ids': [(6, 0, category.ids)],
            })
        Menu = self.env['website.menu'].sudo()
        menu = Menu.search([
            ('website_id', '=', self.website.id), ('url', '=', '/shop'),
        ], limit=1) or Menu.create({
            'name': 'Shop', 'url': '/shop', 'website_id': self.website.id,
            'parent_id': self.website.menu_id.id,
        })
        self.env['theme.utils'].sudo().with_context(
            website_id=self.website.id)._nutivo_build_mega_menu(
                self.website.sudo())
        self.assertTrue(menu.is_mega_menu)
        self.assertEqual(
            menu.mega_menu_content.count('<li>'), NUTIVO_MEGA_MENU_LIMIT - 1)
        self.assertIn('nv-mega__feature', menu.mega_menu_content)

    def test_card_sizes_chips(self):
        """Three chips and a +N chip, none when the card says Options."""
        sizes = [{
            'product_id': index, 'label': 'S%s' % index, 'price_str': '$1',
            'available': True, 'custom_ptav_ids': [],
        } for index in range(5)]
        values = {'sizes': sizes, 'configurable': False}
        render = self.env['ir.qweb'].with_context(
            website_id=self.website.id)._render
        html = str(render('theme_nutivo.card_sizes', {
            'values': values, 'product': self.template}))
        self.assertEqual(html.count('data-size='), 5)
        self.assertIn('nv-size--more', html)
        self.assertIn('+2', html)
        values['configurable'] = True
        html = str(render('theme_nutivo.card_sizes', {
            'values': values, 'product': self.template}))
        self.assertNotIn('nv-size', html)

    def test_quick_view_options(self):
        """The quick view shows the options and the add-ons of a product."""
        with MockRequest(self.env, website=self.website):
            html = NutivoStore().quick_view(self.extra.id)
            self.assertIn('data-extra', html)
            self.assertNotIn('Choose options', html)
            self._add_on()
            html = NutivoStore().quick_view(self.template.sudo().id)
            self.assertIn('nv-addon', html)
            self.assertNotIn('Choose options', html)

    def test_menu_keeps_url(self):
        """A theme menu without page keeps its link as the manual URL."""
        menu = self.env['theme.website.menu'].sudo().create({
            'name': 'Nutivo Menu', 'url': '/nutivo-test',
        })
        values = menu._convert_to_base_model(self.website)
        self.assertEqual(values['manual_url'], '/nutivo-test')
