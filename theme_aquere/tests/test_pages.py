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
"""Tests of the pages and the theme load hooks of the Aquere theme."""
# The tests call the protected theme hooks on purpose.
# pylint: disable=protected-access

from unittest.mock import patch

from odoo.tests import HttpCase, TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAquerePages(HttpCase):
    """Test that every page of the theme renders with the Aquere layout."""

    def setUp(self):
        """Apply the theme on the website the requests are served from."""
        super().setUp()
        website = self.env['website'].search([], limit=1)
        module = self.env['ir.module.module'].search(
            [('name', '=', 'theme_aquere')])
        module.with_context(
            website_id=website.id, apply_new_theme=True,
        )._theme_load(website)

    def test_pages_render(self):
        """Every page answers and wears the Aquere header and wrapper."""
        for url in ('/', '/our-story', '/our-water', '/our-process',
                    '/our-planet', '/contact'):
            response = self.url_open(url)
            self.assertEqual(response.status_code, 200, url)
            self.assertIn('aq-header', response.text, url)
            self.assertIn('aq-wrap', response.text, url)

    def test_contact_form_creates_leads(self):
        """The enquiry form of the contact page posts to the lead model."""
        response = self.url_open('/contact')
        self.assertIn('data-model_name="crm.lead"', response.text)
        self.assertIn('name="contact_name"', response.text)

    def test_header_templates_render(self):
        """Switching the header template keeps the website rendering."""
        website = self.env['website'].search([], limit=1)
        utils = self.env['theme.utils'].with_context(website_id=website.id)
        for xml_id in ('website.template_header_hamburger',
                       'website.template_header_stretch',
                       'website.template_header_default'):
            if self.env.ref(xml_id, raise_if_not_found=False):
                utils.enable_view(xml_id)
                self.assertEqual(self.url_open('/').status_code, 200, xml_id)

    def test_newsletter_is_standard_subscribe_form(self):
        """The newsletter keeps the markup the Odoo subscribe script needs."""
        text = self.url_open('/').text
        for token in ('js_subscribe_value', 'js_subscribe_btn',
                      'js_subscribed_wrap', 'form-control'):
            self.assertIn(token, text)


@tagged('post_install', '-at_install')
class TestAquereThemeLoad(TransactionCase):
    """Test the hooks that set up a website when the theme is chosen."""

    @classmethod
    def setUpClass(cls):
        """Load the theme on a new website once for all the tests."""
        super().setUpClass()
        cls.website = cls.env['website'].create({'name': 'Aquere Test'})
        module = cls.env['ir.module.module'].search(
            [('name', '=', 'theme_aquere')])
        module.with_context(
            website_id=cls.website.id, apply_new_theme=True,
        )._theme_load(cls.website)

    def _views(self):
        """Return the Aquere views copied on the test website."""
        return self.env['ir.ui.view'].with_context(active_test=False).search([
            ('key', '=like', 'theme_aquere.%'),
            ('website_id', '=', self.website.id),
        ])

    def test_header_defaults(self):
        """The header options of the design are active on the website."""
        def active(xml_id):
            return self.env['website'].with_context(
                website_id=self.website.id).viewref(xml_id).active
        for xml_id in ('website.template_header_default',
                       'website.header_visibility_fixed',
                       'website.header_call_to_action',
                       'portal.user_sign_in'):
            self.assertTrue(active(xml_id), xml_id)
        for xml_id in ('website.header_search_box',
                       'website.header_text_element',
                       'website.header_visibility_standard'):
            self.assertFalse(active(xml_id), xml_id)

    def test_logo_and_favicon(self):
        """The logo and the favicon of the brand are set."""
        self.assertTrue(self.website.logo)
        self.assertTrue(self.website.favicon)

    def test_placeholders_are_resolved(self):
        """The newsletter list placeholder is replaced by a real list id."""
        self.assertTrue(self._views())
        for view in self._views():
            self.assertNotIn('aquere_mailing_list', view.arch_db or '')
        # Loading the theme again keeps them resolved.
        module = self.env['ir.module.module'].search(
            [('name', '=', 'theme_aquere')])
        module._theme_load(self.website)
        for view in self._views():
            self.assertNotIn('aquere_mailing_list', view.arch_db or '')

    def test_pages_and_menus(self):
        """The pages overlay the header and the menus keep their links."""
        pages = self.env['website.page'].search([
            ('website_id', '=', self.website.id),
            ('url', 'in', ['/our-story', '/our-water', '/our-process',
                           '/our-planet', '/contact'])])
        self.assertEqual(len(pages), 5)
        self.assertTrue(all(pages.mapped('header_overlay')))
        menus = self.env['website.menu'].search([
            ('website_id', '=', self.website.id),
            ('parent_id', '=', self.website.menu_id.id)])
        self.assertNotIn('/contactus', menus.mapped('url'))
        for menu in menus.filtered(lambda m: m.url.startswith('/our-')):
            self.assertEqual(menu.url, menu.manual_url or menu.url)
            self.assertNotEqual(menu.url, '#')

    def test_menu_without_page_keeps_its_url(self):
        """A theme menu with a URL and no page stores it as manual URL."""
        menu = self.env['theme.website.menu'].create({
            'name': 'Aquere Link',
            'url': '/aquere-link',
        })
        values = menu._convert_to_base_model(self.website)
        self.assertEqual(values.get('manual_url'), '/aquere-link')
        anchor = self.env['theme.website.menu'].create({
            'name': 'Aquere Anchor',
            'url': '/aquere#section',
        })
        self.assertNotIn(
            'manual_url', anchor._convert_to_base_model(self.website))

    def test_other_themes_are_left_alone(self):
        """Loading another module does not resolve the Aquere placeholders."""
        module = self.env['ir.module.module'].search(
            [('name', '=', 'website')])
        base = 'odoo.addons.website.models.ir_module_module.IrModuleModule'
        utils = 'odoo.addons.theme_aquere.models.theme_utils.ThemeUtils'
        with patch(utils + '._aquere_resolve_placeholders') as resolve, \
                patch(base + '._theme_load'):
            module._theme_load(self.website)
        resolve.assert_not_called()
