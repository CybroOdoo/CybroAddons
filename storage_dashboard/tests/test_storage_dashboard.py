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
from unittest.mock import patch

from odoo.exceptions import AccessError
from odoo.tests import HttpCase, TransactionCase, new_test_user, tagged
from odoo.tools import config

from odoo.addons.storage_dashboard.models.storage_usage import (
    CHART_MODEL_LIMIT,
)


@tagged('post_install', '-at_install')
class TestStorageDashboard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Usage = cls.env['storage.usage']

    def test_01_chart_data(self):
        """The chart shows the models using the most storage, the largest
        first, with their size in MB"""
        data = self.Usage.get_data()
        self.assertTrue(data['x_data'])
        self.assertLessEqual(len(data['x_data']), CHART_MODEL_LIMIT)
        self.assertEqual(len(data['x_data']), len(data['y_data']))
        self.assertEqual(data['y_data'], sorted(data['y_data'], reverse=True))
        for name in data['x_data']:
            self.assertIn(name, self.env.registry)
        self.env.cr.execute(
            "SELECT pg_total_relation_size('ir_ui_view') / 1048576.0")
        if self.env.cr.fetchone()[0] > data['y_data'][-1]:
            self.assertIn('ir.ui.view', data['x_data'])

    def test_02_database_info(self):
        """The database, server and configuration information"""
        info = self.Usage.get_info()
        self.assertEqual(info['db_name'], self.env.cr.dbname)
        self.assertIn('PostgreSQL', info['db_version'])
        self.assertTrue(info['db_size'].endswith(' MB'))
        self.assertGreater(info['db_tables'], 100)
        self.assertEqual(info['db_user'], config['db_user'])
        for key in ('total_memory', 'used_memory', 'available_memory'):
            self.assertTrue(info[key].endswith(' GB'))
        self.assertTrue(info['ram_usage'].endswith(' MB'))
        self.assertNotIn('db_password', info)

    def test_03_limits(self):
        """Configuration limits with their unit, Unlimited when not set"""
        options = {
            'limit_memory_soft': 2 * 1024 ** 3,
            'limit_memory_hard': 0,
            'transient_age_limit': 1.0,
            'limit_time_cpu': 60,
            'limit_request': 0,
            'limit_time_real': 0,
            'http_port': 8069,
        }
        with patch.dict(config.options, options):
            info = self.Usage.get_info()
        self.assertEqual(info['soft_limit'], '2.0 GB')
        self.assertEqual(info['hard_limit'], 'Unlimited')
        self.assertEqual(info['transient_age_limit'], '1.0 hours')
        self.assertEqual(info['limit_time_cpu'], '60 s')
        self.assertEqual(info['limit_request'], 'Unlimited')
        self.assertEqual(info['limit_time_real'], 'Unlimited')
        self.assertEqual(info['http_port'], 8069)

    def test_04_not_administrator(self):
        """Users who are not administrators cannot see the dashboard"""
        user = new_test_user(self.env, login='storage_user',
                             groups='base.group_user,base.group_erp_manager')
        usage = self.Usage.with_user(user)
        self.assertFalse(usage.has_access('read'))
        self.assertTrue(self.Usage.with_user(self.env.ref('base.user_admin')).has_access('read'))
        with self.assertRaises(AccessError):
            usage.get_data()
        with self.assertRaises(AccessError):
            usage.get_info()
        menu = self.env.ref('storage_dashboard.storage_dashboard_menu')
        self.assertNotIn(menu.id, self.env['ir.ui.menu'].with_user(
            user)._visible_menu_ids())
        self.assertIn(menu.id, self.env['ir.ui.menu']._visible_menu_ids())


@tagged('post_install', '-at_install')
class TestStorageDashboardTour(HttpCase):

    def test_dashboard_tour(self):
        """The administrator opens the dashboard from the Settings menu"""
        self.start_tour('/odoo/action-storage_dashboard.action_storage_dashboard',
                        'storage_dashboard_tour', login='admin')
