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
import base64
import io

from openpyxl import Workbook

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestUserImport(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.internal_group = cls.env.ref('base.group_user')

    def _make_file(self, row, header=None):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(header or [
            'Name', 'Login', 'Language', 'Company', 'User Type',
            'Groups', 'Technical Settings',
        ])
        sheet.append(row)
        stream = io.BytesIO()
        workbook.save(stream)
        return base64.b64encode(stream.getvalue()).decode()

    def _make_wizard(self, row):
        return self.env['user.import'].create({'file': self._make_file(row)})

    def _valid_row(self, **values):
        row = [
            'Imported User',
            'import_user_excel_test_user',
            'en_US',
            self.env.company.name,
            self.internal_group.full_name,
            '',
            '',
        ]
        columns = {
            'name': 0,
            'login': 1,
            'lang': 2,
            'company': 3,
            'user_type': 4,
            'groups': 5,
            'technical_settings': 6,
        }
        for key, value in values.items():
            row[columns[key]] = value
        return row

    def test_import_creates_user_with_excel_values(self):
        row = self._valid_row()

        self._make_wizard(row).import_file()

        user = self.env['res.users'].search([('login', '=', row[1])])
        self.assertEqual(len(user), 1)
        self.assertEqual(user.name, row[0])
        self.assertEqual(user.lang, row[2])
        self.assertEqual(user.company_id, self.env.company)
        self.assertIn(self.internal_group, user.group_ids)

    def test_import_rejects_inactive_or_unknown_language(self):
        wizard = self._make_wizard(self._valid_row(lang='xx_XX'))

        with self.assertRaisesRegex(ValidationError, 'Language xx_XX is not active'):
            wizard.import_file()

    def test_import_rejects_empty_language_as_validation_error(self):
        wizard = self._make_wizard(self._valid_row(lang=''))

        with self.assertRaisesRegex(ValidationError, r'Language \(empty\) is not active'):
            wizard.import_file()

    def test_import_rejects_unknown_company(self):
        wizard = self._make_wizard(self._valid_row(company='Missing Company'))

        with self.assertRaisesRegex(ValidationError, 'Company Missing Company does not exist'):
            wizard.import_file()

    def test_import_rejects_invalid_user_type_and_group(self):
        invalid_type = self._make_wizard(
            self._valid_row(user_type='Missing User Type')
        )
        with self.assertRaisesRegex(ValidationError, 'Invalid User Type'):
            invalid_type.import_file()

        valid_group_name = self.internal_group.full_name
        invalid_group = self._make_wizard(
            self._valid_row(groups='%s,Missing Group' % valid_group_name)
        )
        with self.assertRaisesRegex(ValidationError, 'Invalid groups Missing Group'):
            invalid_group.import_file()

    def test_import_rejects_empty_user_name(self):
        wizard = self._make_wizard(self._valid_row(name=''))

        with self.assertRaisesRegex(ValidationError, 'Please enter the user name'):
            wizard.import_file()

    def test_import_rejects_invalid_workbook(self):
        wizard = self.env['user.import'].create({
            'file': base64.b64encode(b'not an Excel workbook').decode(),
        })

        with self.assertRaisesRegex(ValidationError, 'Please choose the correct file'):
            wizard.import_file()

    def test_import_skips_empty_trailing_rows(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append([
            'Name', 'Login', 'Language', 'Company', 'User Type',
            'Groups', 'Technical Settings',
        ])
        sheet.append(self._valid_row(login='user_trailing_test'))
        sheet.append([None, None, None, None, None, None, None])
        sheet.append(['', '  ', None, '', None, None, ''])
        stream = io.BytesIO()
        workbook.save(stream)
        file_b64 = base64.b64encode(stream.getvalue()).decode()

        wizard = self.env['user.import'].create({'file': file_b64})
        wizard.import_file()

        user = self.env['res.users'].search([('login', '=', 'user_trailing_test')])
        self.assertEqual(len(user), 1)

    def test_import_for_non_current_company(self):
        other_company = self.env['res.company'].create({'name': 'Other Test Company'})
        row = self._valid_row(
            login='user_other_company',
            company=other_company.name,
        )
        self._make_wizard(row).import_file()

        user = self.env['res.users'].search([('login', '=', 'user_other_company')])
        self.assertEqual(len(user), 1)
        self.assertEqual(user.company_id, other_company)
        self.assertIn(other_company, user.company_ids)

    def test_import_with_user_type_internal_user(self):
        row = self._valid_row(
            login='user_type_internal_user_test',
            user_type='Internal User',
        )
        self._make_wizard(row).import_file()

        user = self.env['res.users'].search([('login', '=', 'user_type_internal_user_test')])
        self.assertEqual(len(user), 1)
        self.assertIn(self.env.ref('base.group_user'), user.group_ids)

    def test_import_with_user_type_portal(self):
        row = self._valid_row(
            login='user_type_portal_test',
            user_type='Portal',
        )
        self._make_wizard(row).import_file()

        user = self.env['res.users'].search([('login', '=', 'user_type_portal_test')])
        self.assertEqual(len(user), 1)
        self.assertIn(self.env.ref('base.group_portal'), user.group_ids)

