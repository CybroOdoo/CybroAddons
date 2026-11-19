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
class TestInstantImportSecurity(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Can read ir.model (like a Mass Mailing user) but cannot create countries.
        cls.limited_user = new_test_user(
            cls.env, login='ii_limited', groups='base.group_user,base.group_erp_manager')
        cls.admin = cls.env.ref('base.user_admin')

    def _import(self, user, model, csv_text, columns):
        attachment = self.env['base_import.import'].with_user(user).create({
            'res_model': model,
            'file': BinaryBytes(csv_text.encode()),
            'file_name': 'data.csv',
            'file_type': 'text/csv',
        })
        cols = [{'name': name, 'fieldInfo': {'id': field, 'fieldPath': field, 'type': ftype}}
                for name, field, ftype in columns]
        return self.env['custom.import.wizard'].with_user(user).copy_import(attachment.id, model, cols)

    def _xml_res_id(self, module, name):
        self.env.cr.execute(
            "SELECT res_id FROM ir_model_data WHERE module = %s AND name = %s", (module, name))
        row = self.env.cr.fetchone()
        return row and row[0]

    def test_import_needs_create_access_on_target(self):
        """A user without create rights on the model cannot import into it."""
        Country = self.env['res.country']
        with self.assertRaises(AccessError):
            Country.with_user(self.limited_user).create({'name': 'Atlantis', 'code': 'QZ'})
        with self.assertRaises(AccessError):
            self._import(self.limited_user, 'res.country', "name,code\nAtlantis,QZ\n",
                         [('name', 'name', 'char'), ('code', 'code', 'char')])
        self.env.invalidate_all()
        self.assertFalse(Country.search_count([('code', '=', 'QZ')]))

    def test_admin_can_import(self):
        """The access check does not block a user who has the rights."""
        result = self._import(self.admin, 'res.country', "name,code\nAtlantis,QZ\n",
                              [('name', 'name', 'char'), ('code', 'code', 'char')])
        self.assertEqual(len(result['inserted_row_ids']), 1)
        self.env.invalidate_all()
        self.assertEqual(self.env['res.country'].search_count([('code', '=', 'QZ')]), 1)

    def test_core_external_id_is_not_hijacked(self):
        """An external ID of another module is refused and keeps its record."""
        before = self._xml_res_id('base', 'main_partner')
        with self.assertRaises(UserError):
            self._import(self.admin, 'res.partner', "id,name\nbase.main_partner,Hijacker\n",
                         [('id', 'id', 'id'), ('name', 'name', 'char')])
        self.assertEqual(self._xml_res_id('base', 'main_partner'), before)

    def test_existing_import_external_id_is_not_moved(self):
        """An existing __import__ external ID is refused, not re-pointed."""
        partner = self.env['res.partner'].create({'name': 'Original'})
        self.env['ir.model.data'].create({
            'module': '__import__', 'name': 'ii_partner', 'model': 'res.partner', 'res_id': partner.id})
        with self.assertRaises(UserError):
            self._import(self.admin, 'res.partner', "id,name\nii_partner,Other\n",
                         [('id', 'id', 'id'), ('name', 'name', 'char')])
        self.assertEqual(self._xml_res_id('__import__', 'ii_partner'), partner.id)

    def test_new_external_id_is_created(self):
        """A new external ID is linked to the imported row."""
        result = self._import(self.admin, 'res.partner', "id,name\nii_new_partner,New One\n",
                              [('id', 'id', 'id'), ('name', 'name', 'char')])
        new_id = result['inserted_row_ids'][0]
        self.assertEqual(self._xml_res_id('__import__', 'ii_new_partner'), new_id)

    def test_database_id_column_is_refused(self):
        """A .id column, at the top or under a one2many, would update existing records."""
        main = self.env.ref('base.main_partner')
        name = main.name
        with self.assertRaises(UserError):
            self._import(self.admin, 'res.partner', f".id,name\n{main.id},Hijacked\n",
                         [('.id', '.id', 'id'), ('name', 'name', 'char')])
        with self.assertRaises(UserError):
            self._import(self.admin, 'res.partner', f"name,child\nII Parent,{main.id}\n",
                         [('name', 'name', 'char'), ('child', 'child_ids/.id', 'id')])
        self.env.invalidate_all()
        self.assertEqual(main.name, name)
        self.assertFalse(main.parent_id)

    def test_link_by_database_id_is_allowed(self):
        """A .id under a many2one only links an existing record."""
        belgium = self.env.ref('base.be')
        result = self._import(self.admin, 'res.partner', f"name,country\nII Linked,{belgium.id}\n",
                              [('name', 'name', 'char'), ('country', 'country_id/.id', 'id')])
        partner = self.env['res.partner'].browse(result['inserted_row_ids'])
        self.assertEqual(partner.country_id, belgium)

    def test_numeric_external_id_is_not_moved(self):
        """An existing external ID made of digits is refused like any other."""
        partner = self.env['res.partner'].create({'name': 'Numbered'})
        self.env['ir.model.data'].create({
            'module': '__import__', 'name': '42', 'model': 'res.partner', 'res_id': partner.id})
        with self.assertRaises(UserError):
            self._import(self.admin, 'res.partner', "id,name\n42,Moved\n",
                         [('id', 'id', 'id'), ('name', 'name', 'char')])
        self.env.invalidate_all()
        self.assertEqual(partner.name, 'Numbered')

    def test_one2many_external_id_is_checked(self):
        """An external ID in a one2many column is refused when it belongs to a module."""
        main = self.env.ref('base.main_partner')
        with self.assertRaises(UserError):
            self._import(self.admin, 'res.partner', "name,child\nII Parent,base.main_partner\n",
                         [('name', 'name', 'char'), ('child', 'child_ids/id', 'id')])
        self.env.invalidate_all()
        self.assertFalse(main.parent_id)
