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
import base64

from odoo.tests import HttpCase, TransactionCase, tagged

# 1x1 transparent PNG
PNG_B64 = ('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk'
           'YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==')
HEADER = 'Scheduled Maintenance In Progress'
MESSAGE = 'We will be back online on Monday'


class MaintenanceCommon:
    """Shared setup: the default website configured for maintenance."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env['website'].search([], limit=1)
        cls.maintenance_vals = {
            'under_maintenance': True,
            'maintenance_hdr': HEADER,
            'maintenance_msg': MESSAGE,
            'maintenance_hdr_color': '#ff0000',
            'maintenance_cont_color': '#0000ff',
            'maintenance_img': PNG_B64,
        }


@tagged('post_install', '-at_install')
class TestWebsiteMaintenanceModels(MaintenanceCommon, TransactionCase):
    """Fields on website and their related settings fields."""

    def test_website_fields_default(self):
        """A website is not under maintenance by default."""
        website = self.env['website'].create({'name': 'Maintenance Test'})
        self.assertFalse(website.under_maintenance)
        self.assertFalse(website.maintenance_hdr)
        self.assertFalse(website.maintenance_msg)

    def test_website_fields_write(self):
        """Maintenance values are stored on the website."""
        self.website.write(self.maintenance_vals)
        self.assertTrue(self.website.under_maintenance)
        self.assertEqual(self.website.maintenance_hdr, HEADER)
        self.assertEqual(self.website.maintenance_msg, MESSAGE)
        self.assertEqual(self.website.maintenance_hdr_color, '#ff0000')
        self.assertEqual(self.website.maintenance_cont_color, '#0000ff')
        self.assertTrue(self.website.maintenance_img)

    def test_settings_write_to_website(self):
        """Saving the settings writes the values to the selected website."""
        settings = self.env['res.config.settings'].create({
            'website_id': self.website.id,
            'is_under_maintenance': True,
            'maintenance_header': HEADER,
            'maintenance_message': MESSAGE,
            'maintenance_hdr_color': '#ff0000',
            'maintenance_cont_color': '#0000ff',
            'maintenance_img': PNG_B64,
        })
        settings.execute()
        self.assertTrue(self.website.under_maintenance)
        self.assertEqual(self.website.maintenance_hdr, HEADER)
        self.assertEqual(self.website.maintenance_msg, MESSAGE)
        self.assertEqual(self.website.maintenance_hdr_color, '#ff0000')
        self.assertEqual(self.website.maintenance_cont_color, '#0000ff')
        self.assertEqual(bytes(self.website.maintenance_img),
                         base64.b64decode(PNG_B64))

    def test_settings_read_from_website(self):
        """Opening the settings shows the website's current values."""
        self.website.write(self.maintenance_vals)
        settings = self.env['res.config.settings'].create({
            'website_id': self.website.id,
        })
        self.assertTrue(settings.is_under_maintenance)
        self.assertEqual(settings.maintenance_header, HEADER)
        self.assertEqual(settings.maintenance_message, MESSAGE)
        self.assertEqual(settings.maintenance_hdr_color, '#ff0000')
        self.assertEqual(settings.maintenance_cont_color, '#0000ff')
        self.assertTrue(settings.maintenance_img)


@tagged('post_install', '-at_install')
class TestWebsiteMaintenancePage(MaintenanceCommon, HttpCase):
    """What public and logged-in visitors see on the website."""

    def test_public_user_sees_maintenance_page(self):
        """Public visitors get the maintenance page instead of the site."""
        self.website.write(self.maintenance_vals)
        response = self.url_open('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(HEADER, response.text)
        self.assertIn(MESSAGE, response.text)
        self.assertIn('o_maintenance_wrap', response.text)
        self.assertIn('color: #ff0000;', response.text)
        self.assertIn('color: #0000ff;', response.text)
        self.assertIn('data:image/png;base64,', response.text)
        self.assertNotIn('id="wrapwrap"', response.text)

    def test_public_user_without_image(self):
        """The maintenance page renders even when no image is set."""
        vals = dict(self.maintenance_vals, maintenance_img=False)
        self.website.write(vals)
        response = self.url_open('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(HEADER, response.text)

    def test_public_user_when_not_under_maintenance(self):
        """With maintenance off, public visitors see the normal website."""
        self.website.write(dict(self.maintenance_vals,
                                under_maintenance=False))
        response = self.url_open('/')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('o_maintenance_wrap', response.text)
        self.assertIn('id="wrapwrap"', response.text)

    def test_login_page_stays_available(self):
        """The login page is never replaced, so staff can still sign in."""
        self.website.write(self.maintenance_vals)
        response = self.url_open('/web/login')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('o_maintenance_wrap', response.text)
        self.assertIn('oe_login_form', response.text)

    def test_logged_in_user_sees_website(self):
        """Signed-in users bypass the maintenance page."""
        self.website.write(self.maintenance_vals)
        self.authenticate('admin', 'admin')
        response = self.url_open('/')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('o_maintenance_wrap', response.text)
        self.assertIn('id="wrapwrap"', response.text)

    def test_maintenance_route_public(self):
        """/maintenance shows the maintenance page to public visitors."""
        self.website.write(self.maintenance_vals)
        response = self.url_open('/maintenance')
        self.assertEqual(response.status_code, 200)
        self.assertIn('o_maintenance_wrap', response.text)
        self.assertIn(HEADER, response.text)

    def test_maintenance_route_logged_in(self):
        """/maintenance renders the preview page for signed-in users."""
        self.website.write(self.maintenance_vals)
        self.authenticate('admin', 'admin')
        response = self.url_open('/maintenance')
        self.assertEqual(response.status_code, 200)
        self.assertIn('o_maintenance_preview', response.text)
        self.assertIn(HEADER, response.text)
        self.assertIn(MESSAGE, response.text)
