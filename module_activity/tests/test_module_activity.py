# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from datetime import datetime

from odoo import exceptions
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestModuleActivity(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.module = self.env['ir.module.module'].create({
            'name': 'x_module_activity_model_test',
            'shortdesc': 'Module Activity Model Test',
            'state': 'installed',
        })

    def test_module_activity_related_fields(self):
        activity = self.env['module.activity'].create({
            'modules_id': self.module.id,
        })

        self.assertEqual(activity.name, 'Module Activity Model Test')
        self.assertEqual(activity.technical_name, 'x_module_activity_model_test')
        self.assertEqual(activity.status, 'installed')

        # Verify dynamic update of related status field
        self.module.state = 'to upgrade'
        self.assertEqual(activity.status, 'to upgrade')

    def test_history_models_store_module_user_and_dates(self):
        activity = self.env['module.activity'].create({
            'modules_id': self.module.id,
            'installed_history_ids': [(0, 0, {
                'installed_module_id': self.module.id,
                'technical_name': self.module.display_name,
                'user_id': self.env.user.id,
                'installed_date': '2026-06-05 01:00:00',
            })],
            'uninstalled_history_ids': [(0, 0, {
                'uninstalled_module_id': self.module.id,
                'technical_name': self.module.display_name,
                'user_id': self.env.user.id,
                'uninstalled_date': '2026-06-05 02:00:00',
            })],
            'upgrade_history_ids': [(0, 0, {
                'upgrade_module_id': self.module.id,
                'technical_name': self.module.display_name,
                'user_id': self.env.user.id,
                'upgrade_date': '2026-06-05 03:00:00',
            })],
        })

        inst_history = activity.installed_history_ids
        uninst_history = activity.uninstalled_history_ids
        upgr_history = activity.upgrade_history_ids

        self.assertEqual(inst_history.installed_module_id, self.module)
        self.assertEqual(inst_history.user_id, self.env.user)
        self.assertEqual(inst_history.technical_name, self.module.display_name)
        self.assertEqual(inst_history.installed_date, datetime(2026, 6, 5, 1, 0, 0))
        self.assertEqual(inst_history.install_id, activity)

        self.assertEqual(uninst_history.uninstalled_module_id, self.module)
        self.assertEqual(uninst_history.user_id, self.env.user)
        self.assertEqual(uninst_history.technical_name, self.module.display_name)
        self.assertEqual(uninst_history.uninstalled_date, datetime(2026, 6, 5, 2, 0, 0))
        self.assertEqual(uninst_history.uninstall_id, activity)

        self.assertEqual(upgr_history.upgrade_module_id, self.module)
        self.assertEqual(upgr_history.user_id, self.env.user)
        self.assertEqual(upgr_history.technical_name, self.module.display_name)
        self.assertEqual(upgr_history.upgrade_date, datetime(2026, 6, 5, 3, 0, 0))
        self.assertEqual(upgr_history.upgrade_id, activity)

    def test_internal_user_access_rights(self):
        """Verify internal users (base.group_user) have read access, but cannot create or edit."""
        standard_user = self.env['res.users'].create({
            'name': 'Standard User',
            'login': 'standard_user_activity_test',
            'email': 'standard_user@test.com',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
        })

        activity = self.env['module.activity'].create({
            'modules_id': self.module.id,
        })

        activity_as_user = activity.with_user(standard_user)
        self.assertEqual(activity_as_user.name, 'Module Activity Model Test')
        self.assertTrue(self.env['module.activity'].with_user(standard_user).search([
            ('id', '=', activity.id),
        ]))

        # Non-admin user cannot create or modify module activities
        with self.assertRaises(exceptions.AccessError):
            self.env['module.activity'].with_user(standard_user).create({
                'modules_id': self.module.id,
            })
        with self.assertRaises(exceptions.AccessError):
            activity_as_user.write({'name': 'Tampered Name'})
        with self.assertRaises(exceptions.AccessError):
            activity_as_user.unlink()

