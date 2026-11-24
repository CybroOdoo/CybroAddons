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
from datetime import date, timedelta

from odoo.tests import HttpCase, TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAeroCourtPages(HttpCase):
    """Test that every page of the theme renders."""

    def setUp(self):
        """Apply the theme to the website, as a user does."""
        super().setUp()
        website = self.env['website'].search([], limit=1)
        self.env['ir.module.module'].search(
            [('name', '=', 'theme_aerocourt')])._theme_load(website)

    def test_pages_render(self):
        """Every page of the theme answers and wears the AeroCourt layout."""
        for url in ('/', '/about', '/booking', '/sessions', '/blog',
                    '/contact'):
            response = self.url_open(url)
            self.assertEqual(response.status_code, 200, url)
            self.assertIn('ac-header', response.text, url)


@tagged('post_install', '-at_install')
class TestAeroCourtRequests(HttpCase):
    """Test that the website forms create CRM leads."""

    def _post(self, route, **params):
        response = self.url_open(
            route, data=json.dumps({'jsonrpc': '2.0', 'method': 'call',
                                    'params': params}),
            headers={'Content-Type': 'application/json'})
        return response.json().get('result', {})

    def test_requests_create_leads(self):
        """Each kind of request creates a tagged lead with a reference."""
        day = str(date.today() + timedelta(days=2))
        base = {'name': 'Test Player', 'phone': '+15550001111'}
        for kind, extra, prefix in (
                ('court', {'date': day, 'slot': '07:00', 'rentalCount': 1},
                 'BK'),
                ('session', {'sessionTitle': 'Open play', 'date': day}, 'SE'),
                ('membership', {'plan': 'Pro'}, 'MB'),
                ('contact', {'message': 'Hello'}, 'CT')):
            result = self._post('/aerocourt/request', kind=kind,
                                **base, **extra)
            self.assertNotIn('error', result, kind)
            self.assertTrue(result['reference'].startswith(prefix), kind)
            lead = self.env['crm.lead'].search(
                [('aerocourt_reference', '=', result['reference'])])
            self.assertEqual(lead.aerocourt_kind, kind)

    def test_court_cannot_be_overbooked(self):
        """Once every court is taken the slot is refused."""
        day = str(date.today() + timedelta(days=3))
        website = self.env['website'].search([], limit=1)
        values = {'kind': 'court', 'date': day, 'slot': '08:00',
                  'name': 'Test Player', 'phone': '+15550001111'}
        for _i in range(website.aerocourt_court_count):
            self.assertNotIn('error', self._post('/aerocourt/request',
                                                 **values))
        self.assertIn('error', self._post('/aerocourt/request', **values))


    def test_request_validation(self):
        """Wrong requests are refused with a message and create no lead."""
        day = str(date.today() + timedelta(days=2))
        website = self.env['website'].search([], limit=1)
        past = str(date.today() - timedelta(days=1))
        far = str(date.today() + timedelta(days=website.aerocourt_booking_days + 5))
        base = {'name': 'Test Player', 'phone': '+15550001111'}
        leads = self.env['crm.lead'].search_count([])
        cases = (
            {'kind': 'unknown', **base},
            {'kind': 'contact', 'name': '', 'phone': ''},
            {'kind': 'contact', 'name': 'Test Player'},
            {'kind': 'contact', 'name': 'Test Player', 'email': 'not-an-email'},
            {'kind': 'court', 'date': past, 'slot': '07:00', **base},
            {'kind': 'court', 'date': far, 'slot': '07:00', **base},
            {'kind': 'court', 'date': 'garbage', 'slot': '07:00', **base},
            {'kind': 'court', 'slot': '07:00', **base},
            {'kind': 'court', 'date': day, 'slot': '03:00', **base},
            {'kind': 'court', 'date': day, 'slot': 'late', **base},
        )
        for params in cases:
            self.assertIn('error', self._post('/aerocourt/request', **params),
                          params)
        self.assertEqual(self.env['crm.lead'].search_count([]), leads)

    def test_bad_numbers_count_as_zero(self):
        """A price or rental count that is not a number is read as zero."""
        day = str(date.today() + timedelta(days=2))
        base = {'name': 'Test Player', 'phone': '+15550001111'}
        session = self._post('/aerocourt/request', kind='session', date=day,
                             sessionTitle='Open play', price='abc', **base)
        lead = self.env['crm.lead'].search(
            [('aerocourt_reference', '=', session['reference'])])
        self.assertEqual(lead.aerocourt_total, 0)
        court = self._post('/aerocourt/request', kind='court', date=day,
                           slot='10:00', rentalCount='many', **base)
        self.assertNotIn('error', court)

    def test_availability(self):
        """The availability route lists the courts taken in a date range."""
        day = date.today() + timedelta(days=4)
        booked = self._post('/aerocourt/request', kind='court', date=str(day),
                            slot='09:00', name='Test Player',
                            phone='+15550001111')
        taken = self._post('/aerocourt/availability', date_from=str(day),
                           date_to=str(day + timedelta(days=1)))
        self.assertEqual(taken[str(day)]['09:00'], [booked['court']])
        empty = self._post('/aerocourt/availability',
                           date_from=str(day + timedelta(days=100)),
                           date_to=str(day + timedelta(days=101)))
        self.assertEqual(empty, {})


@tagged('post_install', '-at_install')
class TestAeroCourtTheme(TransactionCase):
    """Test the setup done when the theme is applied to a website."""

    def setUp(self):
        super().setUp()
        self.website = self.env['website'].search([], limit=1)
        self.env['ir.module.module'].search(
            [('name', '=', 'theme_aerocourt')])._theme_load(self.website)
        self.utils = self.env['theme.utils'].with_context(
            website_id=self.website.id)

    def test_placeholders_are_resolved(self):
        """The newsletter list placeholder of the views is replaced."""
        view = self.env['ir.ui.view'].with_context(active_test=False).search([
            ('key', '=like', 'theme_aerocourt.%'),
            ('website_id', '=', self.website.id),
        ], limit=1)
        head, tail = view.arch_db.rsplit('</', 1)
        view.arch = '%s<!-- aerocourt_mailing_list --></%s' % (head, tail)
        self.assertIn('aerocourt_mailing_list', view.arch_db)
        self.utils._aerocourt_resolve_placeholders(self.website)
        self.assertNotIn('aerocourt_mailing_list', view.arch_db)
        # Loading the theme resolves them as well
        head, tail = view.arch_db.rsplit('</', 1)
        view.arch = '%s<!-- aerocourt_mailing_list --></%s' % (head, tail)
        theme = self.env['ir.module.module'].search(
            [('name', '=', 'theme_aerocourt')])
        theme._theme_load(self.website)
        self.assertNotIn('aerocourt_mailing_list', view.arch_db)

    def test_header_is_configured(self):
        """The header of the design is switched on, the search is left out."""
        self.utils._aerocourt_configure_header()

        def is_active(xml_id):
            view = self.env['ir.ui.view'].with_context(active_test=False).search([
                ('key', '=', xml_id), ('website_id', '=', self.website.id)])
            return bool(view) and view.active

        self.assertTrue(is_active('website.header_visibility_fixed'))
        self.assertFalse(is_active('website.header_search_box'))

    def test_default_menus_are_removed(self):
        """The default Contact and Blog menus give way to the theme ones."""
        menu = self.env['website.menu'].create({
            'name': 'Default contact', 'url': '/contactus',
            'website_id': self.website.id,
            'parent_id': self.website.menu_id.id,
        })
        self.utils._aerocourt_configure_pages(self.website)
        self.assertFalse(menu.exists())

    def test_post_copy_sets_logo(self):
        """The post copy hook gives the website the AeroCourt logo."""
        self.website.logo = False
        self.utils.with_context(website_id=self.website.id)._theme_aerocourt_post_copy(
            self.env['ir.module.module'])
        self.assertTrue(self.website.logo)
        self.assertTrue(self.website.favicon)

    def test_settings_fields(self):
        """The club settings are stored on the website."""
        settings = self.env['res.config.settings'].create({
            'website_id': self.website.id,
            'aerocourt_court_count': 6,
            'aerocourt_open_hour': 7,
        })
        settings.execute()
        self.assertEqual(self.website.aerocourt_court_count, 6)
        self.assertEqual(self.website.aerocourt_open_hour, 7)


@tagged('post_install', '-at_install')
class TestAeroCourtJournal(HttpCase):
    """Test that the Journal is the blog of Odoo."""

    def test_journal_posts(self):
        """The blog lists the sample posts and the old links redirect."""
        blog = self.env.ref('theme_aerocourt.blog_journal')
        self.assertGreaterEqual(len(blog.blog_post_ids), 9)
        response = self.url_open('/blog')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Mastering the Perfect Smash', response.text)
        for old in ('/journal', '/article'):
            response = self.url_open(old, allow_redirects=False)
            self.assertEqual(response.status_code, 301, old)
            self.assertTrue(response.headers['Location'].endswith('/blog'))
