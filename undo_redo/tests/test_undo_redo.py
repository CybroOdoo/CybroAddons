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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestUndoRedo(TransactionCase):
    """Unit test suite for the Undo and Redo module functionality."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.UndoRedo = cls.env['undo.redo']
        cls.Partner = cls.env['res.partner']
        cls.partner = cls.Partner.create({
            'name': 'Test Partner Undo',
            'email': 'test.partner@example.com',
        })

    def test_undo_redo_record_creation(self):
        """Test creating undo.redo transient records directly."""
        record = self.UndoRedo.create({
            'table_name': 'res_partner',
            'record_id': self.partner.id,
            'updated_data': {'name': 'Original Name'},
            'mode': 'undo',
            'user_id': self.env.user.id,
        })
        self.assertTrue(record.id, "Undo record must be created successfully.")
        self.assertEqual(record.table_name, 'res_partner')
        self.assertEqual(record.record_id, self.partner.id)
        self.assertEqual(record.mode, 'undo')
        self.assertEqual(record.user_id, self.env.user)

    def test_get_data_modes_and_ordering(self):
        """Test get_data returns record IDs in descending order for undo and redo."""
        record_1 = self.UndoRedo.create({
            'table_name': 'res_partner',
            'record_id': self.partner.id,
            'updated_data': {'name': 'Version 1'},
            'mode': 'undo',
            'user_id': self.env.user.id,
        })
        record_2 = self.UndoRedo.create({
            'table_name': 'res_partner',
            'record_id': self.partner.id,
            'updated_data': {'name': 'Version 2'},
            'mode': 'undo',
            'user_id': self.env.user.id,
        })
        record_redo = self.UndoRedo.create({
            'table_name': 'res_partner',
            'record_id': self.partner.id,
            'updated_data': {'name': 'Redo Version'},
            'mode': 'redo',
            'user_id': self.env.user.id,
        })

        undo_ids = self.UndoRedo.get_data('res.partner', self.partner.id, mode='undo')
        self.assertIn(record_2.id, undo_ids)
        self.assertIn(record_1.id, undo_ids)
        self.assertNotIn(record_redo.id, undo_ids)
        self.assertLess(
            undo_ids.index(record_2.id),
            undo_ids.index(record_1.id),
            msg="Order check: most recent undo record should appear first.",
        )

        redo_ids = self.UndoRedo.get_data('res_partner', self.partner.id, mode='redo')
        self.assertIn(record_redo.id, redo_ids)
        self.assertNotIn(record_1.id, redo_ids)

    def test_get_data_empty_and_edge_cases(self):
        """Test get_data handles empty or non-existent records safely."""
        self.assertEqual(self.UndoRedo.get_data('', self.partner.id), [])
        self.assertEqual(self.UndoRedo.get_data('res.partner', 0), [])
        self.assertEqual(self.UndoRedo.get_data('non_existent_table', 999999), [])

    def test_undo_redo_unlink_reinsertion(self):
        """Test deleting an undo record executes without crashing."""
        record = self.UndoRedo.create({
            'table_name': 'res_partner',
            'record_id': self.partner.id,
            'updated_data': {'name': 'Restored Name'},
            'mode': 'undo',
            'user_id': self.env.user.id,
        })
        record_id = record.id
        record.unlink()
        remaining = self.UndoRedo.search([('id', '=', record_id)])
        self.assertFalse(remaining, "Undo record should be unlinked.")

    def test_register_hook_execution(self):
        """Test that _register_hook executes without throwing exceptions."""
        try:
            self.UndoRedo._register_hook()
        except Exception as e:
            self.fail(f"_register_hook failed unexpectedly: {e}")

    def test_database_trigger_on_record_update(self):
        """Test modifying a record to ensure triggers execute without crashing."""
        initial_name = self.partner.name
        self.partner.write({'name': 'Modified Partner Name'})
        self.assertEqual(self.partner.name, 'Modified Partner Name')
        self.partner.write({'name': initial_name})
        self.assertEqual(self.partner.name, initial_name)
