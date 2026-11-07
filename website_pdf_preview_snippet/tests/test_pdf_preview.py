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
from unittest.mock import patch

from odoo.tests import HttpCase, tagged

PDF = b'%PDF-1.4\n1 0 obj << /Type /Catalog >> endobj\ntrailer << /Root 1 0 R >>\n%%EOF\n'
URL = '/file/uploaded/'


@tagged('post_install', '-at_install')
class TestPdfPreview(HttpCase):

    def _post(self, files=None, data=None):
        return self.url_open(URL, data=data or {'click_btn': ''}, files=files)

    def test_pdf_is_streamed_back_and_not_stored(self):
        attachments = self.env['ir.attachment'].sudo().search_count([('name', '=', 'ii_report.pdf')])
        response = self._post(files={'attachment': ('ii_report.pdf', PDF, 'application/pdf')})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'application/pdf')
        self.assertIn('inline', response.headers['Content-Disposition'])
        self.assertEqual(response.content, PDF)
        self.assertEqual(
            self.env['ir.attachment'].sudo().search_count([('name', '=', 'ii_report.pdf')]), attachments)

    def test_uppercase_extension_is_accepted(self):
        response = self._post(files={'attachment': ('REPORT.PDF', PDF, 'application/pdf')})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, PDF)

    def test_other_extension_shows_error_page(self):
        response = self._post(files={'attachment': ('notes.txt', b'hello', 'text/plain')})
        self.assertEqual(response.status_code, 400)
        self.assertIn('Only PDF files are allowed.', response.text)
        self.assertIn('<header', response.text, "the error page uses the website layout")

    def test_fake_pdf_is_refused(self):
        response = self._post(files={'attachment': ('evil.pdf', b'<html><script>alert(1)</script>', 'application/pdf')})
        self.assertEqual(response.status_code, 400)
        self.assertIn('not a valid PDF', response.text)

    def test_missing_file_is_a_clean_error(self):
        response = self._post()
        self.assertEqual(response.status_code, 400)
        self.assertIn('Please choose a PDF file.', response.text)

    def test_too_large_file_is_refused(self):
        with patch('odoo.addons.website_pdf_preview_snippet.controllers.main.MAX_PDF_SIZE', 16):
            response = self._post(files={'attachment': ('big.pdf', PDF, 'application/pdf')})
        self.assertEqual(response.status_code, 400)
        self.assertIn('too large', response.text)

    def test_get_is_not_allowed(self):
        response = self.url_open(URL)
        self.assertEqual(response.status_code, 405)

    def test_snippet_is_registered(self):
        arch = self.env.ref('website.snippets').get_combined_arch()
        self.assertIn('website_pdf_preview_snippet.pdf_preview', arch)
        html = str(self.env['ir.qweb']._render('website_pdf_preview_snippet.pdf_preview'))
        self.assertIn('action="/file/uploaded/"', html)
