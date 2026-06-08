# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
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
