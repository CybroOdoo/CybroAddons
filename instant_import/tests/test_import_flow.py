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
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, new_test_user, tagged
from odoo.tools.binary import BinaryBytes


@tagged('post_install', '-at_install')
class TestInstantImportFlow(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Wizard = cls.env['custom.import.wizard']
        cls.belgium = cls.env.ref('base.be')
        cls.tag_a = cls.env['res.partner.category'].create({'name': 'II Tag A'})
        cls.tag_b = cls.env['res.partner.category'].create({'name': 'II Tag B'})

    def _file(self, model, csv_text, user=None):
        Import = self.env['base_import.import']
        if user:
            Import = Import.with_user(user)
        return Import.create({
            'res_model': model,
            'file': BinaryBytes(csv_text.encode()),
            'file_name': 'data.csv',
            'file_type': 'text/csv',
        })

    @staticmethod
    def _columns(*mapping):
        """Columns as the import screen sends them: (header, field path) pairs."""
        columns = []
        for header, path in mapping:
            column = {'name': header}
            if path:
                column['fieldInfo'] = {'id': path.split('/')[-1], 'fieldPath': path}
            columns.append(column)
        return columns

    def test_partners_are_created_through_the_orm(self):
        """Defaults and computed fields are set, so the contacts are visible."""
        attachment = self._file('res.partner', "name,email\nII Alpha,alpha@example.com\nII Beta,\n")
        result = self.Wizard.copy_import(
            attachment.id, 'res.partner', self._columns(('name', 'name'), ('email', 'email')))
        self.assertEqual(result['record_count'], 2)
        self.assertEqual(result['name'], self.env['res.partner']._description)
        partners = self.env['res.partner'].search([('name', 'in', ('II Alpha', 'II Beta'))])
        self.assertEqual(sorted(partners.ids), sorted(result['inserted_row_ids']))
        alpha = partners.filtered(lambda p: p.name == 'II Alpha')
        self.assertTrue(alpha.active)
        self.assertEqual(alpha.commercial_partner_id, alpha)
        self.assertEqual(alpha.email, 'alpha@example.com')

    def test_relational_values_by_name(self):
        """many2one, many2many and one2many columns are resolved by name."""
        csv_text = (
            "name,country,tags,contact\n"
            "II Company,Belgium,\"II Tag A,II Tag B\",II Contact 1\n"
            ",,,II Contact 2\n"
        )
        result = self.Wizard.copy_import(
            self._file('res.partner', csv_text).id, 'res.partner', self._columns(
                ('name', 'name'), ('country', 'country_id'),
                ('tags', 'category_id'), ('contact', 'child_ids/name')))
        self.assertEqual(result['record_count'], 1)
        company = self.env['res.partner'].browse(result['inserted_row_ids'])
        self.assertEqual(company.country_id, self.belgium)
        self.assertEqual(company.category_id, self.tag_a | self.tag_b)
        self.assertEqual(sorted(company.child_ids.mapped('name')), ['II Contact 1', 'II Contact 2'])
        self.assertTrue(all(company.child_ids.mapped('active')))

    def test_unmapped_and_activity_columns_are_ignored(self):
        """Columns without a field, and the activity column, are not imported as fields."""
        result = self.Wizard.copy_import(
            self._file('res.partner', "name,note,activity\nII Gamma,skip me,Call\n").id,
            'res.partner', self._columns(('name', 'name'), ('note', None), ('activity', 'activity_ids')))
        self.assertEqual(result['record_count'], 1)
        self.assertEqual(self.env['res.partner'].browse(result['inserted_row_ids']).name, 'II Gamma')

    def test_error_rolls_back_whole_file(self):
        """A bad row raises and no row of the file is kept."""
        csv_text = "name,country\nII Good,Belgium\nII Bad,No Such Country\n"
        with self.assertRaises(UserError):
            self.Wizard.copy_import(
                self._file('res.partner', csv_text).id, 'res.partner',
                self._columns(('name', 'name'), ('country', 'country_id')))
        self.assertFalse(self.env['res.partner'].search_count([('name', 'in', ('II Good', 'II Bad'))]))

    def test_validate_dry_run(self):
        """The Test button reports errors and never keeps records."""
        good = self._file('res.partner', "name\nII Dry\n")
        columns = self._columns(('name', 'name'))
        self.assertTrue(self.Wizard.validate_columns(good.id, 'res.partner', columns, options={})['is_valid'])
        self.assertFalse(self.env['res.partner'].search_count([('name', '=', 'II Dry')]))
        bad = self._file('res.partner', "name,country\nII Dry,No Such Country\n")
        result = self.Wizard.validate_columns(
            bad.id, 'res.partner', self._columns(('name', 'name'), ('country', 'country_id')), options={})
        self.assertFalse(result['is_valid'])
        self.assertIn('Row 1', result['error_message'])

    def test_validate_mapping(self):
        """Missing mapping and missing required fields are reported."""
        attachment = self._file('res.country', "code\nQZ\n")
        result = self.Wizard.validate_columns(attachment.id, 'res.country', self._columns(('code', None)))
        self.assertEqual(result['error_type'], 'no_fields_mapped')
        result = self.Wizard.validate_columns(attachment.id, 'res.country', self._columns(('code', 'code')))
        self.assertEqual(result['missing_required_fields'], ['name'])
        with self.assertRaises(UserError):
            self.Wizard.copy_import(attachment.id, 'res.country', self._columns(('code', 'code')))

    def test_file_checks(self):
        """The file must exist, hold data and belong to the target model."""
        columns = self._columns(('name', 'name'))
        with self.assertRaises(UserError):
            self.Wizard.copy_import(0, 'res.partner', columns)
        with self.assertRaises(UserError):
            self.Wizard.copy_import(self._file('res.partner.category', "name\nX\n").id, 'res.partner', columns)
        with self.assertRaises(UserError):
            self.Wizard.copy_import(self._file('res.partner', "name\n").id, 'res.partner', columns)

    def test_internal_user_without_rights_is_blocked(self):
        """A plain internal user cannot create tags with the ORM, so neither through the import."""
        user = new_test_user(self.env, login='ii_plain', groups='base.group_user')
        with self.assertRaises(AccessError):
            self.env['res.partner.category'].with_user(user).create({'name': 'II Nope'})
        attachment = self._file('res.partner.category', "name\nII Nope\n", user=user)
        with self.assertRaises(AccessError):
            self.Wizard.with_user(user).copy_import(
                attachment.id, 'res.partner.category', self._columns(('name', 'name')))
        self.assertFalse(self.env['res.partner.category'].search_count([('name', '=', 'II Nope')]))
