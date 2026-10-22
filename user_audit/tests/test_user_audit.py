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
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'user_audit')
class TestUserAudit(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit_model = cls.env['user.audit']
        cls.log_model = cls.env['user.audit.log']
        cls.partner_model = cls.env['ir.model']._get('res.partner')
        cls.audit = cls.audit_model.create({
            'name': 'Partner activity audit',
            'is_create': True,
            'is_read': True,
            'is_write': True,
            'is_delete': True,
            'is_all_users': True,
            'model_ids': [(6, 0, [cls.partner_model.id])],
        })

    def _logs(self):
        return self.log_model.search([
            ('model_id', '=', self.partner_model.id),
        ])

    def test_create_read_write_operations_are_logged(self):
        """Enabled operations create one log with the current user/model."""
        for operation in ('create', 'read', 'write'):
            with self.subTest(operation=operation):
                self.audit_model.create_audit_log(
                    'res.partner', res_id=42, operation_type=operation,
                )
                log = self._logs().filtered(
                    lambda item: item.operation_type == operation
                )
                self.assertEqual(len(log), 1)
                self.assertEqual(log.user_id, self.env.user)
                self.assertEqual(log.record, 42)
                self.assertTrue(log.date)

    def test_delete_logs_each_record_in_a_batch(self):
        self.audit_model.create_audit_log(
            'res.partner', res_id=[11, 12], operation_type='delete',
        )
        logs = self._logs().filtered(
            lambda item: item.operation_type == 'delete'
        )
        self.assertEqual(len(logs), 2)
        self.assertEqual(set(logs.mapped('record')), {11, 12})

    def test_disabled_operation_is_not_logged(self):
        self.audit.write({'is_write': False})
        self.audit_model.create_audit_log(
            'res.partner', res_id=19, operation_type='write',
        )
        self.assertFalse(self._logs())

    def test_only_configured_users_are_logged(self):
        self.audit.write({
            'is_all_users': False,
            'user_ids': [(6, 0, [])],
        })
        self.audit_model.create_audit_log(
            'res.partner', res_id=20, operation_type='create',
        )
        self.assertFalse(self._logs())

    def test_unconfigured_model_and_unknown_model_are_ignored(self):
        self.audit_model.create_audit_log(
            'res.users', res_id=3, operation_type='create',
        )
        self.audit_model.create_audit_log(
            'model.that.does.not.exist', res_id=3,
            operation_type='create',
        )
        self.assertFalse(self._logs())

    def test_log_references_receive_distinct_sequence_names(self):
        logs = self.log_model.create([
            {'user_id': self.env.user.id, 'model_id': self.partner_model.id,
             'operation_type': 'read', 'record': 31},
            {'user_id': self.env.user.id, 'model_id': self.partner_model.id,
             'operation_type': 'read', 'record': 32},
        ])
        self.assertEqual(len(logs), 2)
        self.assertTrue(all(log.name and log.name != 'New' for log in logs))
        self.assertEqual(len(set(logs.mapped('name'))), 2)

    def test_clear_wizard_can_remove_all_logs(self):
        self.audit_model.create_audit_log(
            'res.partner', res_id=51, operation_type='create',
        )
        self.assertTrue(self._logs())
        wizard = self.env['clear.user.log'].create({'full_log': True})
        wizard.action_clear_user_logs()
        self.assertFalse(self._logs())

    def test_clear_wizard_filtered_by_operation_type(self):
        self.audit_model.create_audit_log(
            'res.partner', res_id=61, operation_type='create',
        )
        self.audit_model.create_audit_log(
            'res.partner', res_id=62, operation_type='write',
        )
        self.audit_model.create_audit_log(
            'res.partner', res_id=63, operation_type='read',
        )
        wizard = self.env['clear.user.log'].create({
            'is_create': True,
            'is_write': True,
        })
        wizard.action_clear_user_logs()
        remaining = self._logs().filtered(lambda l: l.record in (61, 62, 63))
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining.operation_type, 'read')

    def test_clear_wizard_filtered_by_model(self):
        self.audit_model.create_audit_log(
            'res.partner', res_id=71, operation_type='create',
        )
        wizard = self.env['clear.user.log'].create({
            'model_id': self.partner_model.id,
        })
        wizard.action_clear_user_logs()
        remaining = self._logs().filtered(lambda l: l.record == 71)
        self.assertFalse(remaining)

    def test_empty_clear_wizard_raises_user_error(self):
        self.audit_model.create_audit_log(
            'res.partner', res_id=81, operation_type='create',
        )
        self.assertTrue(self._logs().filtered(lambda l: l.record == 81))
        wizard = self.env['clear.user.log'].create({})
        with self.assertRaises(UserError):
            wizard.action_clear_user_logs()
        # Verify that logs were not deleted
        self.assertTrue(self._logs().filtered(lambda l: l.record == 81))

    def test_invalid_operation_type_not_logged(self):
        initial_count = len(self._logs())
        self.audit_model.create_audit_log(
            'res.partner', res_id=91, operation_type='hack_operation',
        )
        self.assertEqual(len(self._logs()), initial_count)

    def test_empty_res_id_not_logged(self):
        initial_count = len(self._logs())
        self.audit_model.create_audit_log(
            'res.partner', res_id=False, operation_type='create',
        )
        self.audit_model.create_audit_log(
            'res.partner', res_id=[], operation_type='delete',
        )
        self.assertEqual(len(self._logs()), initial_count)



