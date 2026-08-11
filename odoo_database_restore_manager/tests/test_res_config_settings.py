# -*- coding: utf-8 -*-
###############################################################################
#
#   Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#   Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#   You can modify it under the terms of the GNU AFFERO
#   GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#   You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#   (AGPL v3) along with this program.
#   If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests.common import TransactionCase


class TestResConfigSettings(TransactionCase):
    """Test suite for res.config.settings in odoo_database_restore_manager."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ResConfigSettings = cls.env['res.config.settings']
        cls.params = cls.env['ir.config_parameter'].sudo()

    def test_backup_count_config_parameter(self):
        """Test setting and retrieving backup_count via res.config.settings."""
        config = self.ResConfigSettings.create({
            'backup_count': 10,
        })
        config.execute()

        param_val = self.params.get_param(
            'odoo_database_restore_manager.backup_count'
        )
        self.assertEqual(param_val, '10')

    def test_get_values(self):
        """Test reading backup_count setting from config parameter."""
        self.params.set_param(
            'odoo_database_restore_manager.backup_count', '7'
        )
        config = self.ResConfigSettings.create({})
        config.execute()
        param_val = int(self.params.get_param(
            'odoo_database_restore_manager.backup_count'
        ))
        self.assertEqual(param_val, 7)
