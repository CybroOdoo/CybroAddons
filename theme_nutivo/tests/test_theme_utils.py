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

from odoo.addons.theme_nutivo.models.theme_utils import (
    NUTIVO_TILE_CLASSES,
)


@tagged('post_install', '-at_install')
class TestThemeUtils(TransactionCase):
    """Test the defaults the theme sets when it is applied to a website."""

    @classmethod
    def setUpClass(cls):
        """Create a website and the theme utils bound to it."""
        super().setUpClass()
        cls.website = cls.env['website'].create({'name': 'Nutivo Test'})
        cls.utils = cls.env['theme.utils'].with_context(
            website_id=cls.website.id)

    def test_post_copy(self):
        """Applying the theme sets the shop defaults and the images."""
        self.utils._theme_nutivo_post_copy(
            'theme_nutivo')
        self.assertEqual(self.website.shop_ppr, 3)
        self.assertEqual(
            self.website.shop_opt_products_design_classes,
            NUTIVO_TILE_CLASSES)
        self.assertTrue(self.website.logo)
        self.assertTrue(self.website.favicon)

    def test_resolve_placeholders(self):
        """Placeholders of the theme views are replaced on the website."""
        view = self.env['ir.ui.view'].create({
            'name': 'Nutivo placeholder test',
            'key': 'theme_nutivo.placeholder_test',
            'type': 'qweb',
            'website_id': self.website.id,
            'arch_db': '<div>nutivo_category_mixes</div>',
        })
        self.utils._nutivo_resolve_placeholders(self.website)
        self.assertNotIn('nutivo_category_mixes', view.arch_db)

    def test_resolve_placeholders_with_category(self):
        """A shop category gives its URL."""
        Category = self.env['product.public.category']
        if not Category.search([('name', '=', 'Nuts')], limit=1):
            Category.create({'name': 'Nuts'})
        category = Category.search([('name', '=', 'Nuts')], limit=1)
        view = self.env['ir.ui.view'].create({
            'name': 'Nutivo category test',
            'key': 'theme_nutivo.category_test',
            'type': 'qweb',
            'website_id': self.website.id,
            'arch_db': '<a href="nutivo_category_nuts">x</a>',
        })
        self.utils._nutivo_resolve_placeholders(self.website)
        self.assertIn(category.website_url, view.arch_db)

    def test_remove_default_menus(self):
        """An untouched default blog entry is removed."""
        menu = self.env['website.menu'].create({
            'name': 'Blog',
            'url': '/blog',
            'website_id': self.website.id,
            'parent_id': self.website.menu_id.id,
        })
        self.utils._nutivo_remove_default_menus(self.website)
        self.assertFalse(menu.exists())

    def test_theme_load_resolves_placeholders(self):
        """Loading the theme again, as an update does, resolves the
        placeholders of the views it copies."""
        theme = self.env['ir.module.module'].search(
            [('name', '=', 'theme_nutivo')], limit=1)
        theme._theme_load(self.website)
        views = self.env['ir.ui.view'].with_context(active_test=False).search([
            ('key', '=like', 'theme_nutivo.%'),
            ('website_id', '=', self.website.id),
        ])
        self.assertTrue(views)
        for view in views:
            self.assertNotIn('nutivo_mailing_list', view.arch_db)
            self.assertNotIn('nutivo_category_', view.arch_db)
