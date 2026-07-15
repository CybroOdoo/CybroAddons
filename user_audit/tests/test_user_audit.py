# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from datetime import timedelta
from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestUserAuditLog(TransactionCase):
    """Tests for user.audit.log — sequence generation and field storage."""

    def setUp(self):
        super().setUp()
        self.partner_model = self.env['ir.model'].search(
            [('model', '=', 'res.partner')], limit=1)

    # ------------------------------------------------------------------
    # 1. Sequence / name generation
    # ------------------------------------------------------------------

    def test_log_name_assigned_from_sequence(self):
        """A new log record gets a sequence number, not the default 'New'."""
        log = self.env['user.audit.log'].create({
            'user_id': self.env.user.id,
            'model_id': self.partner_model.id,
            'operation_type': 'create',
            'date': fields.Datetime.now(),
        })
        self.assertNotEqual(log.name, 'New',
            "Sequence should replace the default 'New' name.")
        self.assertTrue(log.name,
            "name must not be empty after create.")

    def test_log_name_unique_across_records(self):
        """Each log record receives a distinct sequence name."""
        vals = {
            'user_id': self.env.user.id,
            'model_id': self.partner_model.id,
            'operation_type': 'write',
            'date': fields.Datetime.now(),
        }
        log1 = self.env['user.audit.log'].create(dict(vals))
        log2 = self.env['user.audit.log'].create(dict(vals))
        self.assertNotEqual(log1.name, log2.name,
            "Two separate log records must have distinct sequence names.")

    # ------------------------------------------------------------------
    # 2. Field storage
    # ------------------------------------------------------------------

    def test_log_stores_operation_type(self):
        """operation_type is persisted correctly for all four values."""
        for op in ('read', 'write', 'create', 'delete'):
            log = self.env['user.audit.log'].create({
                'user_id': self.env.user.id,
                'model_id': self.partner_model.id,
                'operation_type': op,
                'date': fields.Datetime.now(),
            })
            self.assertEqual(log.operation_type, op,
                f"operation_type '{op}' should be stored correctly.")

    def test_log_stores_user(self):
        """user_id is linked correctly."""
        log = self.env['user.audit.log'].create({
            'user_id': self.env.user.id,
            'model_id': self.partner_model.id,
            'operation_type': 'create',
            'date': fields.Datetime.now(),
        })
        self.assertEqual(log.user_id.id, self.env.user.id)

    def test_log_stores_model(self):
        """model_id is linked correctly."""
        log = self.env['user.audit.log'].create({
            'user_id': self.env.user.id,
            'model_id': self.partner_model.id,
            'operation_type': 'delete',
            'date': fields.Datetime.now(),
        })
        self.assertEqual(log.model_id.id, self.partner_model.id)


@tagged('post_install', '-at_install')
class TestUserAudit(TransactionCase):
    """Tests for user.audit — configuration model and audit log generation."""

    def setUp(self):
        super().setUp()
        self.partner_model = self.env['ir.model'].search(
            [('model', '=', 'res.partner')], limit=1)
        self.user_model = self.env['ir.model'].search(
            [('model', '=', 'res.users')], limit=1)

    def _make_audit(self, **kwargs):
        """Create a user.audit config with sensible defaults."""
        defaults = {
            'name': 'Test Audit',
            'is_create': False,
            'is_read': False,
            'is_write': False,
            'is_delete': False,
            'is_all_users': True,
            'model_ids': [(6, 0, [self.partner_model.id])],
        }
        defaults.update(kwargs)
        return self.env['user.audit'].create(defaults)

    def _log_count(self, op_type=None):
        domain = [('operation_type', '=', op_type)] if op_type else []
        return self.env['user.audit.log'].search_count(domain)

    # ------------------------------------------------------------------
    # 3. create_audit_log_for_create
    # ------------------------------------------------------------------

    def test_create_log_created_when_is_create_enabled(self):
        """A log entry is created when is_create=True and model matches."""
        self._make_audit(is_create=True)
        before = self._log_count('create')
        self.env['user.audit'].create_audit_log_for_create('res.partner')
        self.assertEqual(self._log_count('create'), before + 1)

    def test_create_log_not_created_when_is_create_disabled(self):
        """No log entry when is_create=False."""
        self._make_audit(is_create=False)
        before = self._log_count('create')
        self.env['user.audit'].create_audit_log_for_create('res.partner')
        self.assertEqual(self._log_count('create'), before)

    def test_create_log_not_created_for_untracked_model(self):
        """No log entry when the model has no audit configuration."""
        # audit only tracks res.partner; call for res.users
        self._make_audit(is_create=True,
                         model_ids=[(6, 0, [self.partner_model.id])])
        before = self._log_count('create')
        self.env['user.audit'].create_audit_log_for_create('res.users')
        self.assertEqual(self._log_count('create'), before)

    def test_create_log_returns_model_name(self):
        """create_audit_log_for_create returns the model name string."""
        self._make_audit(is_create=True)
        result = self.env['user.audit'].create_audit_log_for_create(
            'res.partner')
        self.assertEqual(result, 'res.partner')

    def test_create_log_operation_type_is_create(self):
        """Log entry has operation_type='create'."""
        self._make_audit(is_create=True)
        self.env['user.audit'].create_audit_log_for_create('res.partner')
        log = self.env['user.audit.log'].search(
            [('operation_type', '=', 'create')], limit=1, order='id desc')
        self.assertTrue(log)
        self.assertEqual(log.operation_type, 'create')

    # ------------------------------------------------------------------
    # 4. create_audit_log_for_read
    # ------------------------------------------------------------------

    def test_read_log_created_when_is_read_enabled(self):
        """A log entry is created when is_read=True and model matches."""
        self._make_audit(is_read=True)
        before = self._log_count('read')
        self.env['user.audit'].create_audit_log_for_read('res.partner', 1)
        self.assertEqual(self._log_count('read'), before + 1)

    def test_read_log_not_created_when_is_read_disabled(self):
        """No log entry when is_read=False."""
        self._make_audit(is_read=False)
        before = self._log_count('read')
        self.env['user.audit'].create_audit_log_for_read('res.partner', 1)
        self.assertEqual(self._log_count('read'), before)

    def test_read_log_stores_record_id(self):
        """Log entry stores the provided record_id."""
        self._make_audit(is_read=True)
        self.env['user.audit'].create_audit_log_for_read('res.partner', 99)
        log = self.env['user.audit.log'].search(
            [('operation_type', '=', 'read'),
             ('record', '=', 99)], limit=1, order='id desc')
        self.assertTrue(log, "Log with record=99 should exist.")
        self.assertEqual(log.record, 99)

    def test_read_log_returns_model_name(self):
        """create_audit_log_for_read returns the model name string."""
        self._make_audit(is_read=True)
        result = self.env['user.audit'].create_audit_log_for_read(
            'res.partner', 1)
        self.assertEqual(result, 'res.partner')

    # ------------------------------------------------------------------
    # 5. create_audit_log_for_write
    # ------------------------------------------------------------------

    def test_write_log_created_when_is_write_enabled(self):
        """A log entry is created when is_write=True and model matches."""
        self._make_audit(is_write=True)
        before = self._log_count('write')
        self.env['user.audit'].create_audit_log_for_write('res.partner', 1)
        self.assertEqual(self._log_count('write'), before + 1)

    def test_write_log_not_created_when_is_write_disabled(self):
        """No log entry when is_write=False."""
        self._make_audit(is_write=False)
        before = self._log_count('write')
        self.env['user.audit'].create_audit_log_for_write('res.partner', 1)
        self.assertEqual(self._log_count('write'), before)

    def test_write_log_returns_model_name(self):
        """create_audit_log_for_write returns the model name string."""
        self._make_audit(is_write=True)
        result = self.env['user.audit'].create_audit_log_for_write(
            'res.partner', 1)
        self.assertEqual(result, 'res.partner')

    def test_write_log_stores_record_id(self):
        """Log entry stores the provided record_id."""
        self._make_audit(is_write=True)
        self.env['user.audit'].create_audit_log_for_write('res.partner', 55)
        log = self.env['user.audit.log'].search(
            [('operation_type', '=', 'write'),
             ('record', '=', 55)], limit=1, order='id desc')
        self.assertTrue(log)
        self.assertEqual(log.record, 55)

    # ------------------------------------------------------------------
    # 6. create_audit_log_for_delete
    # ------------------------------------------------------------------

    def test_delete_log_created_when_is_delete_enabled(self):
        """A log entry is created when is_delete=True and record exists."""
        self._make_audit(is_delete=True)
        # Create a real partner so browse(record_id) is truthy
        partner = self.env['res.partner'].create({'name': 'Audit Delete Test'})
        before = self._log_count('delete')
        self.env['user.audit'].create_audit_log_for_delete(
            'res.partner', partner.id)
        self.assertEqual(self._log_count('delete'), before + 1)

    def test_delete_log_not_created_when_is_delete_disabled(self):
        """No log entry when is_delete=False."""
        self._make_audit(is_delete=False)
        partner = self.env['res.partner'].create({'name': 'No Delete Log'})
        before = self._log_count('delete')
        self.env['user.audit'].create_audit_log_for_delete(
            'res.partner', partner.id)
        self.assertEqual(self._log_count('delete'), before)

    def test_delete_log_not_created_for_zero_record_id(self):
        """
        No log entry when record_id is falsy (0 / False).
        The method guards: if audit and audit.is_delete and record_id and model_id.
        """
        self._make_audit(is_delete=True)
        before = self._log_count('delete')
        self.env['user.audit'].create_audit_log_for_delete('res.partner', 0)
        self.assertEqual(self._log_count('delete'), before)

    def test_delete_log_returns_model_name(self):
        """create_audit_log_for_delete returns the model name string."""
        self._make_audit(is_delete=True)
        partner = self.env['res.partner'].create({'name': 'Return Test'})
        result = self.env['user.audit'].create_audit_log_for_delete(
            'res.partner', partner.id)
        self.assertEqual(result, 'res.partner')


@tagged('post_install', '-at_install')
class TestClearUserLog(TransactionCase):
    """
    Tests for clear.user.log wizard — action_clear_user_logs.
    """

    def setUp(self):
        super().setUp()
        self.partner_model = self.env['ir.model'].search(
            [('model', '=', 'res.partner')], limit=1)
        # Wipe any pre-existing logs so counts are predictable
        self.env['user.audit.log'].search([]).unlink()

    def _make_log(self, op_type, days_ago=0):
        date = fields.Datetime.now() - timedelta(days=days_ago)
        return self.env['user.audit.log'].create({
            'user_id': self.env.user.id,
            'model_id': self.partner_model.id,
            'operation_type': op_type,
            'date': date,
        })

    def _wizard(self, **kwargs):
        return self.env['clear.user.log'].create(kwargs)

    # ------------------------------------------------------------------
    # 7. full_log=True clears everything
    # ------------------------------------------------------------------

    def test_full_log_clears_all_logs(self):
        """full_log=True deletes every log entry regardless of type."""
        for op in ('create', 'read', 'write', 'delete'):
            self._make_log(op)
        self.assertEqual(
            self.env['user.audit.log'].search_count([]), 4)

        self._wizard(full_log=True).action_clear_user_logs()

        self.assertEqual(
            self.env['user.audit.log'].search_count([]), 0,
            "full_log=True should remove all logs.")

    # ------------------------------------------------------------------
    # 8. Single operation-type filters (working branches)
    # ------------------------------------------------------------------

    def test_clear_create_only(self):
        """is_create=True (no date) deletes only 'create' logs."""
        self._make_log('create')
        self._make_log('write')
        self._make_log('read')

        self._wizard(is_create=True).action_clear_user_logs()

        remaining_ops = self.env['user.audit.log'].search([]).mapped(
            'operation_type')
        self.assertNotIn('create', remaining_ops,
            "All 'create' logs should be deleted.")
        self.assertIn('write', remaining_ops)
        self.assertIn('read', remaining_ops)

    def test_clear_read_only(self):
        """is_read=True (no date) deletes only 'read' logs."""
        self._make_log('read')
        self._make_log('create')
        self._wizard(is_read=True).action_clear_user_logs()
        remaining = self.env['user.audit.log'].search([]).mapped(
            'operation_type')
        self.assertNotIn('read', remaining)
        self.assertIn('create', remaining)

    def test_clear_write_only(self):
        """is_write=True (no date) deletes only 'write' logs."""
        self._make_log('write')
        self._make_log('delete')
        self._wizard(is_write=True).action_clear_user_logs()
        remaining = self.env['user.audit.log'].search([]).mapped(
            'operation_type')
        self.assertNotIn('write', remaining)
        self.assertIn('delete', remaining)

    def test_clear_delete_only(self):
        """is_delete=True (no date) deletes only 'delete' logs."""
        self._make_log('delete')
        self._make_log('read')
        self._wizard(is_delete=True).action_clear_user_logs()
        remaining = self.env['user.audit.log'].search([]).mapped(
            'operation_type')
        self.assertNotIn('delete', remaining)
        self.assertIn('read', remaining)

    # ------------------------------------------------------------------
    # 9. to_date + single type (working branches)
    # ------------------------------------------------------------------

    def test_clear_create_before_date(self):
        """to_date + is_create deletes 'create' logs older than to_date."""
        old = self._make_log('create', days_ago=10)
        new = self._make_log('create', days_ago=0)
        self._make_log('write', days_ago=10)

        cutoff = fields.Datetime.now() - timedelta(days=5)
        self._wizard(to_date=cutoff, is_create=True).action_clear_user_logs()

        self.assertFalse(
            self.env['user.audit.log'].browse(old.id).exists(),
            "Old 'create' log should be deleted.")
        self.assertTrue(
            self.env['user.audit.log'].browse(new.id).exists(),
            "Recent 'create' log should survive.")

    def test_clear_delete_before_date(self):
        """to_date + is_delete deletes 'delete' logs older than to_date."""
        old = self._make_log('delete', days_ago=20)
        new = self._make_log('delete', days_ago=1)
        cutoff = fields.Datetime.now() - timedelta(days=10)
        self._wizard(to_date=cutoff, is_delete=True).action_clear_user_logs()
        self.assertFalse(self.env['user.audit.log'].browse(old.id).exists())
        self.assertTrue(self.env['user.audit.log'].browse(new.id).exists())

    def test_clear_read_before_date(self):
        """to_date + is_read deletes 'read' logs older than to_date."""
        old = self._make_log('read', days_ago=15)
        new = self._make_log('read', days_ago=1)
        cutoff = fields.Datetime.now() - timedelta(days=7)
        self._wizard(to_date=cutoff, is_read=True).action_clear_user_logs()
        self.assertFalse(self.env['user.audit.log'].browse(old.id).exists())
        self.assertTrue(self.env['user.audit.log'].browse(new.id).exists())

    def test_clear_write_before_date(self):
        """to_date + is_write deletes 'write' logs older than to_date."""
        old = self._make_log('write', days_ago=30)
        new = self._make_log('write', days_ago=2)
        cutoff = fields.Datetime.now() - timedelta(days=10)
        self._wizard(to_date=cutoff, is_write=True).action_clear_user_logs()
        self.assertFalse(self.env['user.audit.log'].browse(old.id).exists())
        self.assertTrue(self.env['user.audit.log'].browse(new.id).exists())

    def test_clear_by_date_only(self):
        """to_date only (no type flags) deletes all logs older than to_date."""
        old_c = self._make_log('create', days_ago=20)
        old_r = self._make_log('read', days_ago=20)
        new_w = self._make_log('write', days_ago=1)
        cutoff = fields.Datetime.now() - timedelta(days=10)
        self._wizard(to_date=cutoff).action_clear_user_logs()
        self.assertFalse(self.env['user.audit.log'].browse(old_c.id).exists())
        self.assertFalse(self.env['user.audit.log'].browse(old_r.id).exists())
        self.assertTrue(self.env['user.audit.log'].browse(new_w.id).exists())

    # ------------------------------------------------------------------
    # 10. No flags set — fallback clears everything
    # ------------------------------------------------------------------

    def test_no_flags_clears_all(self):
        """
        When no flag and no to_date is set, the else branch runs
        and deletes all logs.
        """
        for op in ('create', 'read', 'write', 'delete'):
            self._make_log(op)
        self.assertEqual(self.env['user.audit.log'].search_count([]), 4)

        self._wizard().action_clear_user_logs()

        self.assertEqual(self.env['user.audit.log'].search_count([]), 0,
            "No-flags fallback should clear all logs.")