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
from urllib.parse import quote

from odoo.tests import HttpCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestReportAttachmentPreview(HttpCase):
    """Test that binary content is served inline for browser preview."""

    @classmethod
    def setUpClass(cls):
        """Create a PDF attachment."""
        super().setUpClass()
        cls.user_admin = cls.env.ref('base.user_admin')
        cls.user_employee = new_test_user(
            cls.env, login='preview_employee', groups='base.group_user')
        cls.attachment = cls.env['ir.attachment'].create({
            'name': 'test_preview.pdf',
            'raw': b'%PDF-1.4\n%%EOF\n',
            'mimetype': 'application/pdf',
            'public': True,
        })

    def _get_disposition(self, url):
        """Fetch ``url`` as admin and return its Content-Disposition."""
        self.authenticate(self.user_admin.login, self.user_admin.login)
        response = self.url_open(url)
        self.assertEqual(response.status_code, 200)
        return response.headers.get('Content-Disposition', '')

    def test_01_content_inline(self):
        """A plain content request is served inline."""
        disposition = self._get_disposition(
            f'/web/content/{self.attachment.id}')
        self.assertTrue(disposition.startswith('inline'), disposition)

    def test_02_download_served_inline(self):
        """A download request is served inline and keeps the file name."""
        disposition = self._get_disposition(
            f'/web/content/{self.attachment.id}?download=true')
        self.assertTrue(disposition.startswith('inline'), disposition)
        self.assertIn('test_preview.pdf', disposition)

    def _create_partner_report(self):
        """Create a PDF report on partners with a print_report_name."""
        return self.env['ir.actions.report'].create({
            'name': 'Partner Card',
            'model': 'res.partner',
            'report_type': 'qweb-pdf',
            'report_name': 'report_attachment_preview.partner_card',
            'print_report_name': "'Card - %s' % object.name",
        })

    def test_03_report_preview_redirects_to_file_name(self):
        """The preview route redirects to a URL ending with the evaluated
        print_report_name, with slashes replaced, keeping the query."""
        report = self._create_partner_report()
        partner = self.env['res.partner'].create({'name': 'Acme/West'})
        self.authenticate(self.user_admin.login, self.user_admin.login)
        response = self.url_open(
            f'/report_attachment_preview/pdf/{report.report_name}/'
            f'{partner.id}?context=%7B%7D',
            allow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertTrue(response.headers['Location'].endswith(
            f'/report_attachment_preview/view/{report.report_name}/'
            f'{partner.id}/Card%20-%20Acme_West.pdf?context=%7B%7D'),
            response.headers['Location'])

    def test_04_report_preview_uses_report_name_for_many_records(self):
        """With several records the file name is the report name."""
        report = self._create_partner_report()
        partners = self.env['res.partner'].create(
            [{'name': 'A'}, {'name': 'B'}])
        self.authenticate(self.user_admin.login, self.user_admin.login)
        response = self.url_open(
            f'/report_attachment_preview/pdf/{report.report_name}/'
            f'{",".join(map(str, partners.ids))}',
            allow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertTrue(response.headers['Location'].endswith(
            '/Partner%20Card.pdf'), response.headers['Location'])

    def test_05_report_preview_view_serves_pdf_inline(self):
        """The view route serves the rendered PDF inline under its name."""
        report = self._create_partner_report()
        partner = self.env['res.partner'].create({'name': 'Acme'})
        self.patch(type(self.env['ir.actions.report']), '_render_qweb_pdf',
                   lambda *args, **kwargs: (b'%PDF-1.4\n%%EOF\n', 'pdf'))
        self.authenticate(self.user_admin.login, self.user_admin.login)
        response = self.url_open(
            f'/report_attachment_preview/view/{report.report_name}/'
            f'{partner.id}/Card%20-%20Acme.pdf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'application/pdf')
        disposition = response.headers['Content-Disposition']
        self.assertTrue(disposition.startswith('inline'), disposition)
        self.assertIn("filename*=UTF-8''Card%20-%20Acme.pdf", disposition)

    def test_06_file_named_attachment_keeps_its_name(self):
        """Only the disposition type changes, never the file name."""
        attachment = self.env['ir.attachment'].create({
            'name': 'attachment.pdf',
            'raw': b'%PDF-1.4\n%%EOF\n',
            'mimetype': 'application/pdf',
            'public': True,
        })
        disposition = self._get_disposition(
            f'/web/content/{attachment.id}?download=true')
        self.assertTrue(disposition.startswith('inline'), disposition)
        self.assertIn('attachment.pdf', disposition)
        disposition = self._get_disposition(f'/web/content/{attachment.id}')
        self.assertIn('attachment.pdf', disposition)

    def test_07_html_keeps_content_security_policy(self):
        """Inline HTML files cannot run scripts in the Odoo session."""
        attachment = self.env['ir.attachment'].create({
            'name': 'page.html',
            'raw': b'<script>alert(1)</script>',
            'mimetype': 'text/html',
            'public': True,
        })
        self.authenticate(self.user_admin.login, self.user_admin.login)
        response = self.url_open(
            f'/web/content/{attachment.id}?download=true')
        self.assertEqual(response.headers['Content-Security-Policy'],
                         "default-src 'none'")
        self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')

    def _capture_report_render(self):
        """Replace the PDF rendering and return the list of contexts and
        data it receives."""
        calls = []

        def render(records, report_ref, res_ids=None, data=None):
            calls.append((dict(records.env.context), data))
            return b'%PDF-1.4\n%%EOF\n', 'pdf'
        self.patch(type(self.env['ir.actions.report']), '_render_qweb_pdf',
                   render)
        return calls

    def test_08_report_context_and_options_reach_the_rendering(self):
        """The context and options of the print action survive the redirect,
        so the preview renders like the default download."""
        report = self._create_partner_report()
        partner = self.env['res.partner'].create({'name': 'Acme'})
        calls = self._capture_report_render()
        self.authenticate(self.user_employee.login, self.user_employee.login)
        context = quote(json.dumps({'preview_flag': 7}))
        options = quote(json.dumps({'date_from': '2026-01-01'}))
        response = self.url_open(
            f'/report_attachment_preview/pdf/{report.report_name}/'
            f'{partner.id}?context={context}&options={options}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(calls[0][0]['preview_flag'], 7)
        self.assertEqual(calls[0][1]['date_from'], '2026-01-01')

    def test_09_report_without_records(self):
        """Reports fed by wizard options have no record ids."""
        report = self._create_partner_report()
        calls = self._capture_report_render()
        self.authenticate(self.user_employee.login, self.user_employee.login)
        response = self.url_open(
            f'/report_attachment_preview/pdf/{report.report_name}')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.url.endswith('/Partner%20Card.pdf'),
                        response.url)
        self.assertEqual(len(calls), 1)

    def test_10_special_characters_in_file_name(self):
        """Accents and URL characters stay inside one URL segment."""
        report = self._create_partner_report()
        partner = self.env['res.partner'].create({'name': 'Café? #1'})
        self._capture_report_render()
        self.authenticate(self.user_employee.login, self.user_employee.login)
        response = self.url_open(
            f'/report_attachment_preview/pdf/{report.report_name}/'
            f'{partner.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(quote('Card - Café? #1.pdf'),
                      response.headers['Content-Disposition'])

    def test_11_unknown_report(self):
        """An unknown report name does not give a file called False.pdf."""
        self.authenticate(self.user_employee.login, self.user_employee.login)
        response = self.url_open(
            '/report_attachment_preview/pdf/no.such_report/1',
            allow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertIn('no.such_report.pdf', response.headers['Location'])

    def test_12_report_requires_login(self):
        """Anonymous visitors are sent to the login page."""
        report = self._create_partner_report()
        self.authenticate(None, None)
        response = self.url_open(
            f'/report_attachment_preview/pdf/{report.report_name}/1',
            allow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertIn('/web/login', response.headers['Location'])
