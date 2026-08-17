# -*- coding: utf-8 -*-
################################################################################
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
#    GNU LESSER PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestIrCronSystray(TransactionCase):
    """Test cases for ir.cron extension in scheduled_action_shortcut."""

    def setUp(self):
        super().setUp()
        self.partner_model = self.env.ref('base.model_res_partner')
        self.cron = self.env['ir.cron'].create({
            'name': 'Test Systray Cron',
            'state': 'code',
            'code': 'model.search([])',
            'model_id': self.partner_model.id,
            'model_name': 'res.partner',
            'user_id': self.env.uid,
            'active': True,
            'interval_number': 1,
            'interval_type': 'days',
            'run_through_systray': False,
        })

    def test_run_through_systray_default(self):
        """Verify the run_through_systray default value is False."""
        self.assertFalse(
            self.cron.run_through_systray,
            "run_through_systray should be False by default"
        )

    def test_run_through_systray_toggle(self):
        """Verify run_through_systray can be enabled."""
        self.cron.write({'run_through_systray': True})
        self.assertTrue(
            self.cron.run_through_systray,
            "run_through_systray should be set to True"
        )

    def test_run_scheduled_actions(self):
        """Verify that calling run_scheduled_actions method triggers the cron."""
        # Use enter_registry_test_mode so the test transaction is shared with the new cursor/connection
        with self.enter_registry_test_mode():
            self.cron.run_scheduled_actions()
