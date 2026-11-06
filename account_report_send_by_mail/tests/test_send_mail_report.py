# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
#    For full details, see https://www.odoo.com/documentation/20.0/legal/licenses/licenses.html
#
#############################################################################
from unittest.mock import MagicMock, patch

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestSendMailReport(TransactionCase):
    """Test suite for send.mail.report wizard."""

    @classmethod
    def setUpClass(cls):
        """Set up test data for send.mail.report."""
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
            'email': 'testpartner@example.com',
        })
        cls.attachment = cls.env['ir.attachment'].create({
            'name': 'test_report.pdf',
            'type': 'binary',
            'raw': b'%PDF-1.4 test report data',
            'mimetype': 'application/pdf',
        })
        cls.report = cls.env['account.report'].search([], limit=1)
        if not cls.report:
            cls.report = cls.env['account.report'].create({
                'name': 'Test Account Report',
            })
        cls.wizard = cls.env['send.mail.report'].create({
            'partner_id': cls.partner.id,
            'subject': 'Accounting Report Subject',
            'email_body': '<p>Please find attached your accounting report.</p>',
            'attachment_ids': [(6, 0, cls.attachment.ids)],
            'report': cls.report.id,
        })

    def test_action_send_report_mail_success(self):
        """Test action_send_report_mail sends email and returns window close action."""
        template = self.env.ref(
            'account_report_send_by_mail.email_template_account_report'
        )
        with patch.object(type(template), 'send_mail') as mock_send_mail:
            action = self.wizard.action_send_report_mail()

            self.assertEqual(action, {'type': 'ir.actions.act_window_close'})
            mock_send_mail.assert_called_once()
            called_args, called_kwargs = mock_send_mail.call_args
            self.assertEqual(called_args[0], self.wizard.id)
            self.assertTrue(called_kwargs.get('force_send'))
            email_values = called_kwargs.get('email_values', {})
            self.assertEqual(email_values.get('subject'), self.wizard.subject)
            self.assertEqual(email_values.get('email_from'), self.env.user.email)
            self.assertFalse(email_values.get('email_to'))

    def test_action_send_report_mail_ensure_one(self):
        """Test action_send_report_mail raises ValueError when called on multi-records."""
        empty_wizard = self.env['send.mail.report'].browse()
        with self.assertRaises(ValueError):
            empty_wizard.action_send_report_mail()

    def test_send_current_report(self):
        """Test send_current_report calls main_function with report_value=False."""
        with patch.object(type(self.wizard), 'main_function', return_value=123) as mock_main:
            result = self.wizard.send_current_report()
            mock_main.assert_called_once_with(False)
            self.assertEqual(result, 123)

    def test_send_unfolded_report(self):
        """Test send_unfolded_report calls main_function with report_value=True."""
        with patch.object(type(self.wizard), 'main_function', return_value=456) as mock_main:
            result = self.wizard.send_unfolded_report()
            mock_main.assert_called_once_with(True)
            self.assertEqual(result, 456)

    def test_main_function_no_report(self):
        """Test main_function returns None when no report ID is available."""
        wizard = self.env['send.mail.report'].create({
            'partner_id': self.partner.id,
            'subject': 'No Report',
            'email_body': '<p>No report</p>',
            'report': False,
        })
        result = wizard.with_context(report=False).main_function(False)
        self.assertIsNone(result)

    def test_main_function_nonexistent_report(self):
        """Test main_function returns None when report ID does not exist."""
        wizard = self.env['send.mail.report'].create({
            'partner_id': self.partner.id,
            'subject': 'Invalid Report',
            'email_body': '<p>Invalid report</p>',
            'report': 99999999,
        })
        result = wizard.main_function(False)
        self.assertIsNone(result)

    def test_main_function_with_wizard_report_field(self):
        """Test main_function uses self.report when context has no report."""
        mock_pdf_data = {
            'file_name': 'Sample_Report.pdf',
            'file_content': b'%PDF-1.4 dummy report content',
        }
        with patch.object(type(self.report), 'dispatch_report_action', return_value=mock_pdf_data) as mock_dispatch:
            attachment_id = self.wizard.with_context(report=False).main_function(False)
            self.assertTrue(attachment_id)
            mock_dispatch.assert_called_once()
            attachment = self.env['ir.attachment'].browse(attachment_id)
            self.assertTrue(attachment.exists())
            self.assertEqual(attachment.name, 'Sample_Report.pdf')
            content = getattr(attachment.raw, 'content', attachment.raw)
            self.assertEqual(content, b'%PDF-1.4 dummy report content')
            self.assertEqual(attachment.mimetype, 'application/pdf')
            self.assertEqual(attachment.res_model, 'account.report')
            self.assertEqual(attachment.res_id, self.report.id)

    def test_main_function_with_context_report_and_unfold_all(self):
        """Test main_function with report_value=True sets unfold_all in options."""
        mock_pdf_data = {
            'file_name': 'Unfolded_Report.pdf',
            'file_content': b'%PDF-1.4 unfolded content',
        }
        wizard = self.env['send.mail.report'].create({
            'partner_id': self.partner.id,
            'subject': 'Context Report',
            'email_body': '<p>Context report</p>',
            'report': False,
        })
        with patch.object(type(self.report), 'get_options', wraps=self.report.get_options) as mock_get_options, \
             patch.object(type(self.report), 'dispatch_report_action', return_value=mock_pdf_data):
            attachment_id = wizard.with_context(report=self.report.id).main_function(True)
            self.assertTrue(attachment_id)
            mock_get_options.assert_called_once()
            _, kwargs = mock_get_options.call_args
            previous_opts = kwargs.get('previous_options', {})
            self.assertTrue(previous_opts.get('unfold_all'))
            self.assertEqual(previous_opts.get('selected_section_id'), self.report.id)

    def test_main_function_with_unfolded_lines_in_context(self):
        """Test main_function with unfolded_lines in context when report_value=False."""
        mock_pdf_data = {
            'file_name': 'Lines_Report.pdf',
            'file_content': b'%PDF-1.4 lines content',
        }
        with patch.object(type(self.report), 'get_options', wraps=self.report.get_options) as mock_get_options, \
             patch.object(type(self.report), 'dispatch_report_action', return_value=mock_pdf_data):
            unfolded_lines = ['line_account_1', 'line_account_2']
            attachment_id = self.wizard.with_context(
                report=self.report.id,
                unfolded_lines=unfolded_lines,
                report_options={'date': {'mode': 'range'}}
            ).main_function(False)
            self.assertTrue(attachment_id)
            mock_get_options.assert_called_once()
            _, kwargs = mock_get_options.call_args
            previous_opts = kwargs.get('previous_options', {})
            self.assertEqual(previous_opts.get('unfolded_lines'), unfolded_lines)
            self.assertEqual(previous_opts.get('date'), {'mode': 'range'})

    def test_main_function_fallback_to_export_to_pdf(self):
        """Test main_function falls back to export_to_pdf if dispatch_report_action fails."""
        mock_pdf_data = {
            'file_name': 'Export_Report',
            'file_content': b'%PDF-1.4 fallback content',
        }
        with patch.object(type(self.report), 'dispatch_report_action', side_effect=Exception("Dispatch failed")), \
             patch.object(type(self.report), 'export_to_pdf', return_value=mock_pdf_data) as mock_export:
            attachment_id = self.wizard.main_function(False)
            self.assertTrue(attachment_id)
            mock_export.assert_called_once()
            attachment = self.env['ir.attachment'].browse(attachment_id)
            # Verifies that '.pdf' extension is appended when missing
            self.assertEqual(attachment.name, 'Export_Report.pdf')
            content = getattr(attachment.raw, 'content', attachment.raw)
            self.assertEqual(content, b'%PDF-1.4 fallback content')

    def test_main_function_default_filename(self):
        """Test main_function defaults file_name to '<report.name>.pdf' if omitted."""
        mock_pdf_data = {
            'file_name': False,
            'file_content': b'%PDF-1.4 unnamed content',
        }
        with patch.object(type(self.report), 'dispatch_report_action', return_value=mock_pdf_data):
            attachment_id = self.wizard.main_function(False)
            self.assertTrue(attachment_id)
            attachment = self.env['ir.attachment'].browse(attachment_id)
            self.assertEqual(attachment.name, f"{self.report.name}.pdf")
