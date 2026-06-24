# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase

class TestUndoRedo(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestUndoRedo, cls).setUpClass()
        cls.bank_model = cls.env['res.bank']
        cls.undo_redo_model = cls.env['undo.redo']

    def test_01_undo_redo_logging(self):
        """Test if updating a record creates an undo log."""
        bank = self.bank_model.create({'name': 'Test Bank Original'})
        
        # Ensure trigger runs
        bank.write({'name': 'Test Bank Updated'})
        self.env.flush_all()
        
        # Check undo log
        logs = self.undo_redo_model.search([
            ('table_name', '=', 'res_bank'),
            ('record_id', '=', bank.id)
        ], order='id desc')
        
        self.assertTrue(logs, "Undo log should be created")
        latest_log = logs[0]
        self.assertEqual(latest_log.mode, 'undo', "Log mode should be 'undo'")
        self.assertIn('name', latest_log.updated_data, "Updated field should be in JSON data")
        self.assertEqual(latest_log.updated_data['name'], 'Test Bank Original', "Original value should be logged")

    def test_02_undo_operation(self):
        """Test if deleting an undo log actually reverts the record."""
        bank = self.bank_model.create({'name': 'Test Bank Original'})
        bank.write({'name': 'Test Bank Updated'})
        self.env.flush_all()
        
        # Find the undo log and delete it to trigger the undo
        log = self.undo_redo_model.search([
            ('table_name', '=', 'res_bank'),
            ('record_id', '=', bank.id),
            ('mode', '=', 'undo')
        ], limit=1, order='id desc')
        self.assertTrue(log)
        
        # Unlink the log
        log.unlink()
        self.env.flush_all()
        
        # Refresh the bank to check if it was reverted
        bank.invalidate_recordset(['name'])
        self.assertEqual(bank.name, 'Test Bank Original', "Bank name should be reverted")

    def test_03_redo_operation(self):
        """Test if deleting a redo log restores the updated record."""
        bank = self.bank_model.create({'name': 'Test Bank Original'})
        bank.write({'name': 'Test Bank Updated'})
        self.env.flush_all()
        
        log = self.undo_redo_model.search([
            ('table_name', '=', 'res_bank'),
            ('record_id', '=', bank.id),
            ('mode', '=', 'undo')
        ], limit=1, order='id desc')
        log.unlink()
        self.env.flush_all()
        
        bank.invalidate_recordset(['name'])
        
        redo_log = self.undo_redo_model.search([
            ('table_name', '=', 'res_bank'),
            ('record_id', '=', bank.id),
            ('mode', '=', 'redo')
        ], limit=1, order='id desc')
        self.assertTrue(redo_log, "Redo log should exist after undo")
        
        redo_log.unlink()
        self.env.flush_all()
        
        bank.invalidate_recordset(['name'])
        self.assertEqual(bank.name, 'Test Bank Updated', "Bank name should be restored to updated value")

    def test_04_delete_record_clears_logs(self):
        """Test if deleting a record removes its undo/redo logs."""
        bank = self.bank_model.create({'name': 'Test Bank Original'})
        bank.write({'name': 'Test Bank Updated'})
        self.env.flush_all()
        
        logs_before = self.undo_redo_model.search([
            ('table_name', '=', 'res_bank'),
            ('record_id', '=', bank.id)
        ])
        self.assertTrue(logs_before, "Logs should exist before deletion")
        
        bank.unlink()
        self.env.flush_all()
        
        logs_after = self.undo_redo_model.search([
            ('table_name', '=', 'res_bank'),
            ('record_id', '=', bank.id)
        ])
        self.assertFalse(logs_after, "Logs should be deleted when the record is deleted")

    def test_05_get_data(self):
        """Test the get_data method of undo.redo model."""
        bank = self.bank_model.create({'name': 'Test Bank Original'})
        bank.write({'name': 'Test Bank Updated'})
        self.env.flush_all()
        
        undo_ids = self.undo_redo_model.get_data('res.bank', bank.id, 'undo')
        self.assertTrue(undo_ids, "get_data should return undo log IDs")
        
        # Verify the returned ID is correct
        log = self.undo_redo_model.browse(undo_ids[0])
        self.assertEqual(log.table_name, 'res_bank')
        self.assertEqual(log.record_id, bank.id)
        self.assertEqual(log.mode, 'undo')
