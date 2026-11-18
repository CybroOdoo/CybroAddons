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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPropelleTheme(TransactionCase):
    """Test what the theme sets up on a website."""

    @classmethod
    def setUpClass(cls):
        """Apply the theme to the website."""
        super().setUpClass()
        cls.website = cls.env['website'].search([], limit=1)
        cls.theme = cls.env['ir.module.module'].search(
            [('name', '=', 'theme_propelle')], limit=1)
        cls.theme._theme_load(cls.website)

    def test_menus_keep_their_link(self):
        """A menu without page keeps its URL after the theme is loaded."""
        urls = {
            menu.name: menu.url for menu in self.env['website.menu'].search([
                ('website_id', '=', self.website.id),
                ('theme_template_id', '!=', False)])}
        for name, url in (('Buy', '/buy'), ('Rent', '/rent'),
                          ('Projects', '/projects')):
            self.assertEqual(urls.get(name), url, name)

    def test_menu_loaded_once(self):
        """Loading the theme again does not duplicate the menus."""
        self.theme._theme_load(self.website)
        buy = self.env['website.menu'].search([
            ('website_id', '=', self.website.id), ('name', '=', 'Buy'),
            ('url', '=', '/buy')])
        self.assertEqual(len(buy), 1)

    def test_header_defaults(self):
        """The sign in link and the call to action are on, the search off."""
        utils = self.env['theme.utils'].with_context(
            website_id=self.website.id)
        utils._propelle_configure_header()
        def active(key):
            """Whether the view of the key is enabled on the website."""
            return self.website.with_context(
                website_id=self.website.id).is_view_active(key)
        self.assertTrue(active('portal.user_sign_in'))
        self.assertTrue(active('website.header_call_to_action'))
        self.assertFalse(active('website.header_search_box'))
        self.assertFalse(active('website.header_text_element'))

    def test_placeholders_resolved(self):
        """No Propelle view keeps the mailing list placeholder."""
        views = self.env['ir.ui.view'].with_context(
            active_test=False).search([
                ('key', '=like', 'theme_propelle.%'),
                ('website_id', '=', self.website.id)])
        self.assertTrue(views)
        for view in views:
            self.assertNotIn('propelle_mailing_list', view.arch_db or '')
