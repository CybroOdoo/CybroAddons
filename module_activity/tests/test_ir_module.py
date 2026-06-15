# -*- coding: utf-8 -*-

from uuid import uuid4
from unittest.mock import patch

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestIrModuleActivity(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Module = cls.env['ir.module.module']
        cls.Activity = cls.env['module.activity']

    def _create_test_module(self):
        module_name = 'test_module_activity_%s' % uuid4().hex
        return self.Module.create({
            'name': module_name,
            'shortdesc': module_name.replace('_', ' ').title(),
            'state': 'uninstalled',
        })

    def _activity_for(self, module):
        return self.Activity.search([('modules_id', '=', module.id)], limit=1)

    def test_button_immediate_install_creates_install_history(self):
        module = self._create_test_module()
        before = fields.Datetime.now()

        with patch(
            'odoo.addons.base.models.ir_module.Module.button_immediate_install',
            return_value={'type': 'ir.actions.act_window_close'},
        ) as super_install:
            result = module.button_immediate_install()

        super_install.assert_called_once()
        self.assertEqual(result, {'type': 'ir.actions.act_window_close'})
        activity = self._activity_for(module)
        self.assertTrue(activity)
        self.assertEqual(len(activity.installed_history_ids), 1)
        install_history = activity.installed_history_ids
        self.assertEqual(install_history.installed_module_id, module)
        self.assertEqual(install_history.technical_name, module.display_name)
        self.assertEqual(install_history.user_id, self.env.user)
        self.assertGreaterEqual(install_history.installed_date, before)

    def test_button_immediate_install_appends_to_existing_activity(self):
        module = self._create_test_module()
        activity = self.Activity.create({'modules_id': module.id})

        with patch(
            'odoo.addons.base.models.ir_module.Module.button_immediate_install',
            return_value=True,
        ):
            module.button_immediate_install()

        self.assertEqual(self._activity_for(module), activity)
        self.assertEqual(len(activity.installed_history_ids), 1)
        self.assertEqual(
            activity.installed_history_ids.installed_module_id,
            module,
        )

    def test_button_immediate_uninstall_creates_uninstall_history(self):
        module = self._create_test_module()
        before = fields.Datetime.now()

        with patch(
            'odoo.addons.base.models.ir_module.Module.button_immediate_uninstall',
            return_value={'type': 'ir.actions.client'},
        ) as super_uninstall:
            result = module.button_immediate_uninstall()

        super_uninstall.assert_called_once()
        self.assertEqual(result, {'type': 'ir.actions.client'})
        activity = self._activity_for(module)
        self.assertTrue(activity)
        self.assertEqual(len(activity.uninstalled_history_ids), 1)
        uninstall_history = activity.uninstalled_history_ids
        self.assertEqual(uninstall_history.uninstalled_module_id, module)
        self.assertEqual(uninstall_history.technical_name, module.display_name)
        self.assertEqual(uninstall_history.user_id, self.env.user)
        self.assertGreaterEqual(uninstall_history.uninstalled_date, before)

    def test_button_immediate_uninstall_appends_to_existing_activity(self):
        module = self._create_test_module()
        activity = self.Activity.create({'modules_id': module.id})

        with patch(
            'odoo.addons.base.models.ir_module.Module.button_immediate_uninstall',
            return_value=True,
        ):
            module.button_immediate_uninstall()

        self.assertEqual(self._activity_for(module), activity)
        self.assertEqual(len(activity.uninstalled_history_ids), 1)
        self.assertEqual(
            activity.uninstalled_history_ids.uninstalled_module_id,
            module,
        )

    def test_button_immediate_upgrade_creates_upgrade_history(self):
        module = self._create_test_module()
        before = fields.Datetime.now()

        with patch(
            'odoo.addons.base.models.ir_module.Module.button_immediate_upgrade',
            return_value={'type': 'ir.actions.act_window_close'},
        ) as super_upgrade:
            result = module.button_immediate_upgrade()

        super_upgrade.assert_called_once()
        self.assertEqual(result, {'type': 'ir.actions.act_window_close'})
        activity = self._activity_for(module)
        self.assertTrue(activity)
        self.assertEqual(len(activity.upgrade_history_ids), 1)
        upgrade_history = activity.upgrade_history_ids
        self.assertEqual(upgrade_history.upgrade_module_id, module)
        self.assertEqual(upgrade_history.technical_name, module.display_name)
        self.assertEqual(upgrade_history.user_id, self.env.user)
        self.assertGreaterEqual(upgrade_history.upgrade_date, before)

    def test_button_immediate_upgrade_appends_to_existing_activity(self):
        module = self._create_test_module()
        activity = self.Activity.create({'modules_id': module.id})

        with patch(
            'odoo.addons.base.models.ir_module.Module.button_immediate_upgrade',
            return_value=True,
        ):
            module.button_immediate_upgrade()

        self.assertEqual(self._activity_for(module), activity)
        self.assertEqual(len(activity.upgrade_history_ids), 1)
        self.assertEqual(activity.upgrade_history_ids.upgrade_module_id, module)

    def test_module_activity_module_is_not_logged(self):
        module = self.Module.search([('name', '=', 'module_activity')], limit=1)
        activity = self._activity_for(module)
        install_count = len(activity.installed_history_ids)
        uninstall_count = len(activity.uninstalled_history_ids)
        upgrade_count = len(activity.upgrade_history_ids)

        with patch(
            'odoo.addons.base.models.ir_module.Module.button_immediate_install',
            return_value=True,
        ):
            module.button_immediate_install()
        with patch(
            'odoo.addons.base.models.ir_module.Module.button_immediate_uninstall',
            return_value=True,
        ):
            module.button_immediate_uninstall()
        with patch(
            'odoo.addons.base.models.ir_module.Module.button_immediate_upgrade',
            return_value=True,
        ):
            module.button_immediate_upgrade()

        activity = self._activity_for(module)
        self.assertEqual(len(activity.installed_history_ids), install_count)
        self.assertEqual(len(activity.uninstalled_history_ids), uninstall_count)
        self.assertEqual(len(activity.upgrade_history_ids), upgrade_count)
