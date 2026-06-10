# -*- coding: utf-8 -*-
from odoo.tests import common


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

        self.assertEqual(activity.installed_history_ids.installed_module_id, self.module)
        self.assertEqual(activity.installed_history_ids.user_id, self.env.user)
        self.assertEqual(activity.uninstalled_history_ids.uninstalled_module_id, self.module)
        self.assertEqual(activity.uninstalled_history_ids.user_id, self.env.user)
        self.assertEqual(activity.upgrade_history_ids.upgrade_module_id, self.module)
        self.assertEqual(activity.upgrade_history_ids.user_id, self.env.user)
