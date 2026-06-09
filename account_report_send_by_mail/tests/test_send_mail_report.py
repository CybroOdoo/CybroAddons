# -*- coding: utf-8 -*-
################################################################################
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
from unittest.mock import patch
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestSendMailReport(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
            'email': 'test@test.com',
        })

        cls.report = cls.env['account.report'].search(
            [],
            limit=1
        )

        cls.wizard = cls.env['send.mail.report'].create({
            'partner_id': cls.partner.id,
            'subject': 'Test Subject',
            'email_body': 'Test Body',
            'report': cls.report.id,
        })

    def test_wizard_creation(self):
        """Ensure wizard fields are properly assigned."""

        self.assertEqual(
            self.wizard.partner_id,
            self.partner
        )

        self.assertEqual(
            self.wizard.subject,
            'Test Subject'
        )

    @patch(
        'odoo.addons.account_report_send_by_mail.'
        'wizard.send_mail_report.SendMailReport.main_function'
    )
    def test_send_current_report(
            self,
            mock_main_function
    ):
        """Ensure current report method calls main function."""

        mock_main_function.return_value = 1

        result = (
            self.wizard
            .with_context(
                report=self.report.id,
                unfolded_lines=[]
            )
            .send_current_report()
        )

        self.assertEqual(result, 1)

        mock_main_function.assert_called_once()

    @patch(
        'odoo.addons.account_report_send_by_mail.'
        'wizard.send_mail_report.SendMailReport.main_function'
    )
    def test_send_unfolded_report(
            self,
            mock_main_function
    ):
        """Ensure unfolded report method calls main function."""

        mock_main_function.return_value = 1

        result = (
            self.wizard
            .with_context(report=self.report.id)
            .send_unfolded_report()
        )

        self.assertEqual(result, 1)

        mock_main_function.assert_called_once()

    def test_action_send_report_mail(self):
        """Ensure mail action executes."""

        attachment = self.env['ir.attachment'].create({
            'name': 'test.pdf',
            'type': 'binary',
            'datas': b'dGVzdA==',
            'mimetype': 'application/pdf',
        })

        self.wizard.attachment_ids = [(
            4,
            attachment.id
        )]
        result = self.wizard.action_send_report_mail()
        self.assertFalse(result)
