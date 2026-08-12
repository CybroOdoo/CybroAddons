# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):
    """Test suite for Hikvision integration configuration settings."""

    def test_hikvision_config_settings(self):
        """Test configuration parameter persistence and menu visibility update."""
        config = self.env['res.config.settings'].create({
            'enable_hr_approval': True,
            'minimum_working_hours': 7.5,
        })
        config.execute()

        get_param = self.env['ir.config_parameter'].sudo().get_param
        self.assertEqual(get_param('hikvision_odoo_integration.enable_hr_approval'), 'True')
        self.assertEqual(get_param('hikvision_odoo_integration.minimum_working_hours'), '7.5')

        approval_group = self.env.ref('hikvision_odoo_integration.group_attendance_approval_menu', raise_if_not_found=False)
        if approval_group:
            self.assertTrue(len(approval_group.users) > 0)

        # Now disable approval
        config_disable = self.env['res.config.settings'].create({
            'enable_hr_approval': False,
            'minimum_working_hours': 8.0,
        })
        config_disable.execute()

        self.assertEqual(get_param('hikvision_odoo_integration.enable_hr_approval'), 'False')
        if approval_group:
            self.assertEqual(len(approval_group.users), 0)
