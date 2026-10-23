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
from lxml import etree
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestWebsiteCustomContactUs(common.TransactionCase):
    """Test suite for website_custom_contact_us module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country_us = cls.env.ref('base.us', raise_if_not_found=False)
        cls.company = cls.env['res.company'].create({
            'name': 'Test Contact Company',
            'street': '123 Test Street',
            'street2': 'Suite 400',
            'city': 'San Francisco',
            'zip': '94102',
            'phone': '+1 555-123-4567',
            'email': 'contact@testcompany.com',
            'website': 'https://www.testcompany.com',
            'vat': 'US123456789',
            'country_id': cls.country_us.id if cls.country_us else False,
            'social_facebook': 'https://facebook.com/testcompany',
            'social_twitter': 'https://twitter.com/testcompany',
            'social_linkedin': 'https://linkedin.com/company/testcompany',
            'social_instagram': 'https://instagram.com/testcompany',
            'social_github': 'https://github.com/testcompany',
        })
        cls.website = cls.env['website'].create({
            'name': 'Test Contact Website',
            'company_id': cls.company.id,
        })
        # Prepare test view containing our xpath's template arch
        view = cls.env.ref('website_custom_contact_us.website_contact_template_inherited')
        tree = etree.fromstring(view.arch)
        xpath_elem = tree.find('.//xpath')
        inner_xml = ''.join(etree.tostring(c, encoding='unicode') for c in xpath_elem)
        cls.contact_test_view = cls.env['ir.ui.view'].create({
            'name': 'test_contactus_inner_view',
            'type': 'qweb',
            'arch': f'<t t-name="test_contactus_inner_view">{inner_xml}</t>',
        })

    def _render_contact_template(self):
        """Render the inner contact us template with current website settings."""
        return self.env['ir.qweb']._render(self.contact_test_view.id, {'website': self.website})

    def test_default_values(self):
        """Test default boolean values on website record."""
        website = self.website
        self.assertTrue(website.is_company, "is_company should default to True")
        self.assertTrue(website.is_address, "is_address should default to True")
        self.assertTrue(website.is_phone, "is_phone should default to True")
        self.assertTrue(website.is_email, "is_email should default to True")
        self.assertTrue(website.is_website, "is_website should default to True")
        self.assertTrue(website.is_vat, "is_vat should default to True")
        self.assertTrue(website.is_country_flag, "is_country_flag should default to True")
        self.assertTrue(website.is_show_phone_icon, "is_show_phone_icon should default to True")
        self.assertFalse(website.is_address_in_oneline, "is_address_in_oneline should default to False")
        self.assertFalse(website.is_hide_marker_icons, "is_hide_marker_icons should default to False")
        self.assertTrue(website.is_facebook, "is_facebook should default to True")
        self.assertTrue(website.is_twitter, "is_twitter should default to True")
        self.assertTrue(website.is_linkedin, "is_linkedin should default to True")
        self.assertTrue(website.is_instagram, "is_instagram should default to True")
        self.assertTrue(website.is_github, "is_github should default to True")

    def test_toggle_visibility_options(self):
        """Test toggling all company data visibility options."""
        website = self.website
        website.write({
            'is_company': False,
            'is_address': False,
            'is_phone': False,
            'is_email': False,
            'is_website': False,
            'is_vat': False,
            'is_country_flag': False,
            'is_address_in_oneline': True,
            'is_hide_marker_icons': True,
            'is_show_phone_icon': False,
            'is_facebook': False,
            'is_twitter': False,
            'is_linkedin': False,
            'is_instagram': False,
            'is_github': False,
        })
        self.assertFalse(website.is_company)
        self.assertFalse(website.is_address)
        self.assertFalse(website.is_phone)
        self.assertFalse(website.is_email)
        self.assertFalse(website.is_website)
        self.assertFalse(website.is_vat)
        self.assertFalse(website.is_country_flag)
        self.assertTrue(website.is_address_in_oneline)
        self.assertTrue(website.is_hide_marker_icons)
        self.assertFalse(website.is_show_phone_icon)
        self.assertFalse(website.is_facebook)
        self.assertFalse(website.is_twitter)
        self.assertFalse(website.is_linkedin)
        self.assertFalse(website.is_instagram)
        self.assertFalse(website.is_github)

    def test_social_links_related_fields(self):
        """Test reading and writing related social media fields."""
        website = self.website
        self.assertEqual(website.social_facebook, self.company.social_facebook)
        self.assertEqual(website.social_twitter, self.company.social_twitter)
        self.assertEqual(website.social_linkedin, self.company.social_linkedin)
        self.assertEqual(website.social_instagram, self.company.social_instagram)
        self.assertEqual(website.social_github, self.company.social_github)

        website.write({
            'social_facebook': 'https://facebook.com/newfb',
            'social_twitter': 'https://twitter.com/newx',
            'social_linkedin': 'https://linkedin.com/company/newin',
            'social_instagram': 'https://instagram.com/newinsta',
            'social_github': 'https://github.com/newgit',
        })
        self.assertEqual(self.company.social_facebook, 'https://facebook.com/newfb')
        self.assertEqual(self.company.social_twitter, 'https://twitter.com/newx')
        self.assertEqual(self.company.social_linkedin, 'https://linkedin.com/company/newin')
        self.assertEqual(self.company.social_instagram, 'https://instagram.com/newinsta')
        self.assertEqual(self.company.social_github, 'https://github.com/newgit')

    def test_template_rendering_default(self):
        """Test rendering contactus template with default configuration."""
        rendered = self._render_contact_template()
        self.assertIn('Test Contact Company', rendered)
        self.assertIn('123 Test Street', rendered)
        self.assertIn('+1 555-123-4567', rendered)
        self.assertIn('contact@testcompany.com', rendered)
        self.assertIn('https://www.testcompany.com', rendered)
        self.assertIn('US123456789', rendered)
        self.assertIn('data-icon="phone"', rendered)
        self.assertIn('https://facebook.com/testcompany', rendered)

    def test_template_rendering_oneline_address(self):
        """Test rendering contactus template with single-line address."""
        self.website.write({'is_address_in_oneline': True})
        rendered = self._render_contact_template()
        self.assertIn('123 Test Street', rendered)
        self.assertIn('San Francisco', rendered)

    def test_template_rendering_address_disabled(self):
        """Test that address is not displayed when is_address=False even if is_address_in_oneline=True."""
        self.website.write({
            'is_address': False,
            'is_address_in_oneline': True,
        })
        rendered = self._render_contact_template()
        self.assertNotIn('123 Test Street', rendered)
        self.assertNotIn('San Francisco', rendered)

    def test_template_rendering_hide_icons(self):
        """Test that icons are hidden when is_hide_marker_icons=True."""
        self.website.write({'is_hide_marker_icons': True})
        rendered = self._render_contact_template()
        self.assertNotIn('data-icon="location_on"', rendered)
        self.assertNotIn('data-icon="phone"', rendered)
        self.assertNotIn('data-icon="mail"', rendered)
        self.assertNotIn('data-icon="public"', rendered)

    def test_template_rendering_hide_phone_icon_only(self):
        """Test hiding phone icon while keeping marker icons visible."""
        self.website.write({
            'is_hide_marker_icons': False,
            'is_show_phone_icon': False,
        })
        rendered = self._render_contact_template()
        self.assertIn('data-icon="location_on"', rendered)
        self.assertNotIn('data-icon="phone"', rendered)
        self.assertIn('+1 555-123-4567', rendered)

    def test_template_rendering_all_disabled(self):
        """Test rendering with all toggles disabled does not leave empty li tags or content."""
        self.website.write({
            'is_company': False,
            'is_address': False,
            'is_phone': False,
            'is_email': False,
            'is_website': False,
            'is_vat': False,
            'is_country_flag': False,
            'is_facebook': False,
            'is_twitter': False,
            'is_linkedin': False,
            'is_instagram': False,
            'is_github': False,
        })
        rendered = self._render_contact_template()
        self.assertNotIn('Test Contact Company', rendered)
        self.assertNotIn('123 Test Street', rendered)
        self.assertNotIn('+1 555-123-4567', rendered)
        self.assertNotIn('contact@testcompany.com', rendered)
        self.assertNotIn('US123456789', rendered)
        self.assertNotIn('https://facebook.com/testcompany', rendered)
        # Verify no empty <li> tags are generated
        compact = rendered.replace(' ', '').replace('\n', '')
        self.assertNotIn('<li></li>', compact)

    def test_inherited_view_architecture(self):
        """Test that the inherited template targets website.contactus and replaces img."""
        view = self.env.ref('website_custom_contact_us.website_contact_template_inherited')
        self.assertEqual(view.inherit_id, self.env.ref('website.contactus'))
        tree = etree.fromstring(view.arch)
        xpath = tree.find('.//xpath')
        self.assertIsNotNone(xpath)
        self.assertEqual(xpath.get('expr'), "//img[hasclass('img')]")
        self.assertEqual(xpath.get('position'), "replace")
