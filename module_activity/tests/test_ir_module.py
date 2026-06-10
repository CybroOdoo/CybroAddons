# -*- coding: utf-8 -*-
from unittest.mock import patch

from odoo.addons.base.models import ir_module as base_ir_module
from odoo.tests import common


class TestIrModuleActivity(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.tracking_module = self.env['ir.module.module'].search([
            ('name', '=', 'module_activity'),
        ], limit=1)
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
        self.assertEqual(activity.installed_history_ids.installed_module_id, self.module)
        self.assertEqual(activity.installed_history_ids.user_id, self.env.user)

    def test_button_immediate_install_appends_history_to_existing_activity(self):
        activity = self.env['module.activity'].create({'modules_id': self.module.id})

        with patch.object(
            base_ir_module.IrModuleModule,
            'button_immediate_install',
            return_value=True,
        ):
            self.module.button_immediate_install()

        self.assertEqual(self._activity(), activity)
        self.assertEqual(len(activity.installed_history_ids), 1)

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
        self.assertEqual(activity.uninstalled_history_ids.uninstalled_module_id, self.module)
        self.assertEqual(activity.uninstalled_history_ids.user_id, self.env.user)

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
        self.assertEqual(activity.upgrade_history_ids.upgrade_module_id, self.module)
        self.assertEqual(activity.upgrade_history_ids.user_id, self.env.user)

    def test_module_activity_itself_is_not_logged(self):
        with patch.object(
            base_ir_module.IrModuleModule,
            'button_immediate_upgrade',
            return_value=True,
        ):
            self.tracking_module.button_immediate_upgrade()

        self.assertFalse(self._activity(self.tracking_module))
