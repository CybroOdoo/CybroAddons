# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(
#    <https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from unittest.mock import patch
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestCronFailureNotification(TransactionCase):
    """Test suite verifying models, reports, cron failure tracking,
    and failure email notifications.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.module = cls.env['ir.module.module'].search([
            ('name', '=', 'cron_failure_notification'),
        ], limit=1)

        cls.erp_manager_group = cls.env.ref('base.group_erp_manager')
        cls.test_manager = cls.env['res.users'].create({
            'name': 'Test Cron Admin',
            'login': 'cron_admin_test',
            'email': 'cron_admin@example.com',
            'group_ids': [(6, 0, [cls.erp_manager_group.id])],
        })

    def test_01_module_installed(self):
        """Verify module installation and state."""
        self.assertTrue(self.module, "Module must be found in database.")
        self.assertEqual(
            self.module.state,
            'installed',
            "Module state should be installed.",
        )

    def test_02_manifest_metadata(self):
        """Verify manifest required fields and valid configurations."""
        self.assertEqual(self.module.author, 'Cybrosys Techno Solutions')
        self.assertEqual(self.module.license, 'LGPL-3')
        self.assertTrue(self.module.summary)
        self.assertTrue(self.module.description)

    def test_03_failure_history_crud(self):
        """Verify failure.history model CRUD and field operations."""
        record = self.env['failure.history'].create({
            'name': 'Test Failed Cron Job',
            'error': 'ValueError: Sample error traceback message',
        })
        self.assertTrue(record.id)
        self.assertEqual(record.name, 'Test Failed Cron Job')
        self.assertIn('Sample error', record.error)
        self.assertTrue(record.create_date)

        # Update and search
        record.write({'name': 'Updated Failed Cron'})
        self.assertEqual(record.name, 'Updated Failed Cron')

        found = self.env['failure.history'].search([
            ('id', '=', record.id),
        ])
        self.assertEqual(len(found), 1)

    def test_04_cron_callback_failure_logging(self):
        """Verify _callback records failure history when a job fails."""
        cron = self.env['ir.cron'].create({
            'name': 'Failing Test Cron Job',
            'model_id': self.env.ref('base.model_res_partner').id,
            'state': 'code',
            'code': 'model.search([])',
            'interval_number': 1,
            'interval_type': 'days',
            'active': True,
        })
        server_action_id = cron.ir_actions_server_id.id
        our_cls = next(
            c for c in type(cron).__mro__
            if 'cron_failure_notification' in c.__module__
        )
        mro_list = list(type(cron).__mro__)
        target_cls = next(
            c for c in mro_list[mro_list.index(our_cls) + 1:]
            if '_callback' in c.__dict__
        )

        callback_failed = False
        with patch.object(
            target_cls,
            '_callback',
            side_effect=ValueError("Simulated cron crash"),
        ):
            try:
                cron._callback(cron.name, server_action_id)
            except ValueError:
                callback_failed = True

        self.assertTrue(
            callback_failed,
            "_callback should propagate exception raised during execution.",
        )

        failure_record = self.env['failure.history'].search([
            ('name', '=', 'Failing Test Cron Job'),
        ], limit=1)
        self.assertTrue(
            failure_record,
            "Failure history record should be created when cron crashes.",
        )
        self.assertIn(
            'Simulated cron crash',
            failure_record.error,
        )

    def test_05_mail_send_cron_no_failures(self):
        """Verify mail_send_cron returns False when no failures exist."""
        self.env['failure.history'].search([]).unlink()
        cron_model = self.env['ir.cron']
        result = cron_model.mail_send_cron()
        self.assertFalse(
            result,
            "mail_send_cron should return False when no failures exist.",
        )

    def test_06_mail_send_cron_with_failures(self):
        """Verify mail_send_cron triggers email sending when failures exist."""
        self.env['failure.history'].create({
            'name': 'Production Backup Cron',
            'error': 'ConnectionTimeout: Failed to reach remote storage',
        })
        cron_model = self.env['ir.cron']

        with patch.object(
            type(self.env['mail.template']), 'send_mail', return_value=123
        ) as mock_send:
            res = cron_model.mail_send_cron()
            self.assertTrue(
                res,
                "mail_send_cron should return True when failures exist.",
            )
            mock_send.assert_called_once()
            call_kwargs = mock_send.call_args.kwargs
            self.assertIn('email_values', call_kwargs)
            self.assertIn(
                'cron_admin@example.com',
                call_kwargs['email_values']['email_to'],
            )

    def test_07_pdf_report_rendering(self):
        """Verify the QWeb PDF failure report renders without errors."""
        self.env['failure.history'].create({
            'name': 'Report Test Cron',
            'error': 'ZeroDivisionError: division by zero',
        })
        cron = self.env['ir.cron'].search([], limit=1)
        pdf_content, ext = self.env['ir.actions.report']._render_qweb_pdf(
            'cron_failure_notification.cron_fail_pdf_report',
            [cron.id],
        )
        self.assertTrue(pdf_content)
        self.assertIn(ext, ('pdf', 'html'))

    def test_08_access_rights(self):
        """Verify security access rules for failure.history model."""
        history_as_manager = self.env['failure.history'].with_user(
            self.test_manager
        )
        rec = history_as_manager.create({
            'name': 'Manager Created Record',
            'error': 'Test error',
        })
        self.assertTrue(rec.id)
        self.assertTrue(rec.read(['name', 'error']))
        rec.unlink()

        # Regular user without erp_manager group
        regular_user = self.env['res.users'].create({
            'name': 'Test Regular User',
            'login': 'regular_user_test',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        history_as_user = self.env['failure.history'].with_user(regular_user)
        # Regular user can read
        existing = self.env['failure.history'].create({
            'name': 'User Readable Record',
            'error': 'User error',
        })
        read_res = history_as_user.browse(existing.id).read(['name'])
        self.assertEqual(read_res[0]['name'], 'User Readable Record')
