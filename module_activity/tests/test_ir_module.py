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

from unittest.mock import patch

from odoo.addons.base.models import ir_module as base_ir_module
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestIrModuleActivity(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.tracking_module = self.env['ir.module.module'].search([
            ('name', '=', 'module_activity'),
        ], limit=1)
        if not self.tracking_module:
            self.tracking_module = self.env['ir.module.module'].create({
                'name': 'module_activity',
                'shortdesc': 'Module Activation Details',
                'state': 'installed',
            })
        else:
            self.tracking_module.write({'state': 'installed'})

        self.module = self.env['ir.module.module'].create({
            'name': 'x_module_activity_action_test_%s' % self._testMethodName,
            'shortdesc': 'Module Activity Action Test',
            'state': 'installed',
        })

    def _activity(self, module=None):
        return self.env['module.activity'].search([
            ('modules_id', '=', (module or self.module).id),
        ], limit=1)

    def test_button_immediate_install_creates_activity_and_install_history(self):
        with patch.object(
            base_ir_module.IrModuleModule,
            'button_immediate_install',
            return_value={'type': 'ir.actions.client'},
        ):
            result = self.module.button_immediate_install()

        activity = self._activity()
        self.assertEqual(result, {'type': 'ir.actions.client'})
        self.assertEqual(activity.modules_id, self.module)
        self.assertEqual(len(activity.installed_history_ids), 1)
        history = activity.installed_history_ids
        self.assertEqual(history.installed_module_id, self.module)
        self.assertEqual(history.user_id, self.env.user)
        self.assertEqual(history.technical_name, self.module.display_name)
        self.assertTrue(history.installed_date)

    def test_button_immediate_install_appends_history_to_existing_activity(self):
        activity = self.env['module.activity'].create({'modules_id': self.module.id})

        with patch.object(
            base_ir_module.IrModuleModule,
            'button_immediate_install',
            return_value=True,
        ):
            self.module.button_immediate_install()
            self.module.button_immediate_install()

        self.assertEqual(self._activity(), activity)
        self.assertEqual(len(activity.installed_history_ids), 2)

    def test_button_immediate_uninstall_creates_activity_and_uninstall_history(self):
        with patch.object(
            base_ir_module.IrModuleModule,
            'button_immediate_uninstall',
            return_value={'type': 'ir.actions.client'},
        ):
            result = self.module.button_immediate_uninstall()

        activity = self._activity()
        self.assertEqual(result, {'type': 'ir.actions.client'})
        self.assertEqual(activity.modules_id, self.module)
        self.assertEqual(len(activity.uninstalled_history_ids), 1)
        history = activity.uninstalled_history_ids
        self.assertEqual(history.uninstalled_module_id, self.module)
        self.assertEqual(history.user_id, self.env.user)
        self.assertEqual(history.technical_name, self.module.display_name)
        self.assertTrue(history.uninstalled_date)

    def test_button_immediate_uninstall_appends_history_to_existing_activity(self):
        activity = self.env['module.activity'].create({'modules_id': self.module.id})

        with patch.object(
            base_ir_module.IrModuleModule,
            'button_immediate_uninstall',
            return_value=True,
        ):
            self.module.button_immediate_uninstall()
            self.module.button_immediate_uninstall()

        self.assertEqual(self._activity(), activity)
        self.assertEqual(len(activity.uninstalled_history_ids), 2)

    def test_button_immediate_upgrade_creates_activity_and_upgrade_history(self):
        with patch.object(
            base_ir_module.IrModuleModule,
            'button_immediate_upgrade',
            return_value={'type': 'ir.actions.client'},
        ):
            result = self.module.button_immediate_upgrade()

        activity = self._activity()
        self.assertEqual(result, {'type': 'ir.actions.client'})
        self.assertEqual(activity.modules_id, self.module)
        self.assertEqual(len(activity.upgrade_history_ids), 1)
        history = activity.upgrade_history_ids
        self.assertEqual(history.upgrade_module_id, self.module)
        self.assertEqual(history.user_id, self.env.user)
        self.assertEqual(history.technical_name, self.module.display_name)
        self.assertTrue(history.upgrade_date)

    def test_button_immediate_upgrade_appends_history_to_existing_activity(self):
        activity = self.env['module.activity'].create({'modules_id': self.module.id})

        with patch.object(
            base_ir_module.IrModuleModule,
            'button_immediate_upgrade',
            return_value=True,
        ):
            self.module.button_immediate_upgrade()
            self.module.button_immediate_upgrade()

        self.assertEqual(self._activity(), activity)
        self.assertEqual(len(activity.upgrade_history_ids), 2)

    def test_module_activity_itself_is_not_logged(self):
        with patch.object(
            base_ir_module.IrModuleModule,
            'button_immediate_install',
            return_value=True,
        ), patch.object(
            base_ir_module.IrModuleModule,
            'button_immediate_uninstall',
            return_value=True,
        ), patch.object(
            base_ir_module.IrModuleModule,
            'button_immediate_upgrade',
            return_value=True,
        ):
            self.tracking_module.button_immediate_install()
            self.tracking_module.button_immediate_uninstall()
            self.tracking_module.button_immediate_upgrade()

        self.assertFalse(self._activity(self.tracking_module))

    def test_button_immediate_install_when_tracking_module_not_installed(self):
        self.tracking_module.write({'state': 'uninstalled'})

        with patch.object(
            base_ir_module.IrModuleModule,
            'button_immediate_install',
            return_value=True,
        ):
            self.module.button_immediate_install()

        self.assertFalse(self._activity())

    def test_multi_module_action(self):
        module_2 = self.env['ir.module.module'].create({
            'name': 'x_module_activity_action_test_2',
            'shortdesc': 'Module Activity Action Test 2',
            'state': 'installed',
        })
        modules = self.module | module_2

        with patch.object(
            base_ir_module.IrModuleModule,
            'button_immediate_upgrade',
            return_value=True,
        ):
            modules.button_immediate_upgrade()

        activity_1 = self._activity(self.module)
        activity_2 = self._activity(module_2)
        self.assertTrue(activity_1)
        self.assertTrue(activity_2)
        self.assertEqual(len(activity_1.upgrade_history_ids), 1)
        self.assertEqual(len(activity_2.upgrade_history_ids), 1)

    def test_standard_button_install_creates_activity(self):
        with patch.object(
            base_ir_module.IrModuleModule,
            'button_install',
            return_value=True,
        ):
            self.module.button_install()

        activity = self._activity()
        self.assertTrue(activity)
        self.assertEqual(len(activity.installed_history_ids), 1)
        self.assertEqual(activity.installed_history_ids.installed_module_id, self.module)

    def test_standard_button_uninstall_creates_activity(self):
        with patch.object(
            base_ir_module.IrModuleModule,
            'button_uninstall',
            return_value=True,
        ):
            self.module.button_uninstall()

        activity = self._activity()
        self.assertTrue(activity)
        self.assertEqual(len(activity.uninstalled_history_ids), 1)
        self.assertEqual(activity.uninstalled_history_ids.uninstalled_module_id, self.module)

    def test_standard_button_upgrade_creates_activity(self):
        with patch.object(
            base_ir_module.IrModuleModule,
            'button_upgrade',
            return_value=True,
        ):
            self.module.button_upgrade()

        activity = self._activity()
        self.assertTrue(activity)
        self.assertEqual(len(activity.upgrade_history_ids), 1)
        self.assertEqual(activity.upgrade_history_ids.upgrade_module_id, self.module)
