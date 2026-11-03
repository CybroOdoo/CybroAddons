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
from io import BytesIO
from unittest.mock import patch

from odoo.tools.pdf import PdfReader, PdfWriter

from odoo.tests.common import HttpCase, TransactionCase, tagged

REPORT_MODEL = 'odoo.addons.base.models.ir_actions_report.IrActionsReport'


def _blank_pdf(pages=1):
    """Return the content of a blank PDF with the given number of pages."""
    writer = PdfWriter()
    for _i in range(pages):
        writer.add_blank_page(width=200, height=200)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


@tagged('post_install', '-at_install')
class TestPdfReportPasswordProtection(TransactionCase):
    """Tests for the password protection of report actions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.report_model = cls.env['ir.actions.report']
        cls.blank_pdf_content = _blank_pdf()
        cls.report_action = cls.report_model.create({
            'name': 'Test Protected Report',
            'model': 'res.partner',
            'report_name': 'test_protected_report',
            'report_type': 'qweb-pdf',
            'is_password': True,
            'password_name': 'secure_password_123',
        })

    def test_01_apply_password_protection_enabled(self):
        """The PDF is encrypted when is_password is True."""
        encrypted_pdf = self.report_action.apply_password_protection(
            self.blank_pdf_content, 'ignored_pwd')
        reader = PdfReader(BytesIO(encrypted_pdf))
        self.assertTrue(reader.is_encrypted,
                        "The PDF should be encrypted when is_password is True.")
        self.assertTrue(reader.decrypt('secure_password_123'),
                        "The PDF should open with the correct password.")

    def test_02_apply_password_protection_disabled(self):
        """The PDF stays unencrypted when is_password is False."""
        self.report_action.is_password = False
        pdf = self.report_action.apply_password_protection(
            self.blank_pdf_content, 'ignored_pwd')
        reader = PdfReader(BytesIO(pdf))
        self.assertFalse(reader.is_encrypted,
                         "The PDF should not be encrypted when is_password "
                         "is False.")

    def test_03_wrong_password_fails(self):
        """The encrypted PDF does not open with a wrong password."""
        encrypted_pdf = self.report_action.apply_password_protection(
            self.blank_pdf_content, 'ignored_pwd')
        reader = PdfReader(BytesIO(encrypted_pdf))
        self.assertFalse(reader.decrypt('wrong_password'),
                         "The PDF should not open with a wrong password.")

    def test_04_second_argument_is_ignored(self):
        """The stored password is used, not the second argument."""
        encrypted_pdf = self.report_action.apply_password_protection(
            self.blank_pdf_content, 'other_password')
        reader = PdfReader(BytesIO(encrypted_pdf))
        self.assertFalse(reader.decrypt('other_password'))
        reader = PdfReader(BytesIO(encrypted_pdf))
        self.assertTrue(reader.decrypt('secure_password_123'))

    def test_05_pages_are_preserved(self):
        """All pages are kept after encryption."""
        pdf = _blank_pdf(pages=3)
        encrypted_pdf = self.report_action.apply_password_protection(pdf, '')
        reader = PdfReader(BytesIO(encrypted_pdf))
        reader.decrypt('secure_password_123')
        self.assertEqual(len(reader.pages), 3)

    def test_06_disabled_keeps_pages(self):
        """All pages are kept when protection is disabled."""
        self.report_action.is_password = False
        pdf = _blank_pdf(pages=2)
        result = self.report_action.apply_password_protection(pdf, '')
        self.assertEqual(len(PdfReader(BytesIO(result)).pages), 2)

    def test_07_password_change_is_used(self):
        """A changed password is applied to new PDFs."""
        self.report_action.password_name = 'new_password'
        encrypted_pdf = self.report_action.apply_password_protection(
            self.blank_pdf_content, '')
        reader = PdfReader(BytesIO(encrypted_pdf))
        self.assertFalse(reader.decrypt('secure_password_123'))
        reader = PdfReader(BytesIO(encrypted_pdf))
        self.assertTrue(reader.decrypt('new_password'))

    def test_08_field_defaults(self):
        """Password protection is disabled by default."""
        report = self.report_model.create({
            'name': 'Plain Report',
            'model': 'res.partner',
            'report_name': 'test_plain_report',
            'report_type': 'qweb-pdf',
        })
        self.assertFalse(report.is_password)
        self.assertFalse(report.password_name)

    def test_09_fields_in_form_view(self):
        """The password fields are added to the report form view."""
        view = self.report_model.get_view(
            view_id=self.env.ref('base.act_report_xml_view').id)
        self.assertIn('name="is_password"', view['arch'])
        self.assertIn('name="password_name"', view['arch'])

    def test_10_password_field_is_char(self):
        """The password field is a Char and the flag is a Boolean."""
        fields_info = self.report_model.fields_get(
            ['is_password', 'password_name'])
        self.assertEqual(fields_info['is_password']['type'], 'boolean')
        self.assertEqual(fields_info['password_name']['type'], 'char')


@tagged('post_install', '-at_install')
class TestPdfReportPasswordController(HttpCase):
    """Tests for the report controller."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pdf_content = _blank_pdf()
        report_model = cls.env['ir.actions.report']
        cls.protected_report = report_model.create({
            'name': 'Protected Report',
            'model': 'res.partner',
            'report_name': 'test_protected_report',
            'report_type': 'qweb-pdf',
            'is_password': True,
            'password_name': 'secret',
        })
        cls.plain_report = report_model.create({
            'name': 'Plain Report',
            'model': 'res.partner',
            'report_name': 'test_plain_report',
            'report_type': 'qweb-pdf',
        })

    def _get(self, url, **patches):
        """Open the URL as admin with the given report methods mocked."""
        self.authenticate('admin', 'admin')
        mocks = [patch(f'{REPORT_MODEL}.{name}', return_value=value)
                 for name, value in patches.items()]
        for mock in mocks:
            mock.start()
        try:
            return self.url_open(url)
        finally:
            for mock in mocks:
                mock.stop()

    def test_01_protected_pdf_is_encrypted(self):
        """The controller serves an encrypted PDF for protected reports."""
        response = self._get('/report/pdf/test_protected_report/1',
                             _render_qweb_pdf=(self.pdf_content, 'pdf'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'application/pdf')
        self.assertEqual(int(response.headers['Content-Length']),
                         len(response.content))
        reader = PdfReader(BytesIO(response.content))
        self.assertTrue(reader.is_encrypted)
        self.assertTrue(reader.decrypt('secret'))

    def test_02_plain_pdf_is_not_encrypted(self):
        """The controller serves a normal PDF for unprotected reports."""
        response = self._get('/report/pdf/test_plain_report/1',
                             _render_qweb_pdf=(self.pdf_content, 'pdf'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(PdfReader(BytesIO(response.content)).is_encrypted)

    def test_03_multiple_docids(self):
        """Several record ids in the URL are accepted."""
        response = self._get('/report/pdf/test_protected_report/1,2,3',
                             _render_qweb_pdf=(self.pdf_content, 'pdf'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(PdfReader(BytesIO(response.content)).is_encrypted)

    def test_04_pdf_without_docids(self):
        """A report without record ids is served and encrypted."""
        response = self._get('/report/pdf/test_protected_report',
                             _render_qweb_pdf=(self.pdf_content, 'pdf'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(PdfReader(BytesIO(response.content)).is_encrypted)

    def test_05_html_is_not_encrypted(self):
        """HTML output is returned as it is."""
        response = self._get('/report/html/test_protected_report/1',
                             _render_qweb_html=(b'<p>Hello</p>', 'html'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'<p>Hello</p>')

    def test_06_text_is_not_encrypted(self):
        """Text output is returned as it is."""
        response = self._get('/report/text/test_protected_report/1',
                             _render_qweb_text=('Hello', 'text'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'text/plain')
        self.assertEqual(response.text, 'Hello')

    def test_07_unknown_converter_is_rejected(self):
        """An unknown converter returns an error message, not a report."""
        self.authenticate('admin', 'admin')
        response = self.url_open('/report/unknown/test_protected_report/1')
        self.assertIn('Converter unknown not implemented', response.text)

    def test_08_context_and_options_are_read(self):
        """The context and options parameters are decoded."""
        captured = {}

        def fake_render(report, report_ref, docids, data=None):
            captured['lang'] = report.env.context.get('lang')
            captured['docids'] = docids
            captured['data'] = data
            return self.pdf_content, 'pdf'

        self.authenticate('admin', 'admin')
        options = json.dumps({'extra': 'value'})
        context = json.dumps({'lang': 'en_US'})
        with patch(f'{REPORT_MODEL}._render_qweb_pdf', autospec=True,
                   side_effect=fake_render):
            response = self.url_open(
                '/report/pdf/test_protected_report/1,2'
                f'?options={options}&context={context}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(captured['docids'], [1, 2])
        self.assertEqual(captured['lang'], 'en_US')
        self.assertEqual(captured['data'].get('extra'), 'value')
