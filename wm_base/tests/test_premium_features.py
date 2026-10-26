#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPremiumFeatures(TransactionCase):

    def test_settings_show_premium_cards(self):
        arch = self.env['res.config.settings'].get_views([(False, 'form')])['views']['form']['arch']
        self.assertIn('wm_premium_card', arch)
        self.assertIn('module_wm_subscription', arch)
        self.assertIn('module_wm_driver_app', arch)

    def test_dialog_content_for_every_feature(self):
        for feature in ('subscription', 'subscription_plan', 'driver_app'):
            wizard = self.env['wm.premium.feature.wizard'].create({'feature': feature})
            self.assertTrue(wizard.title, feature)
            self.assertTrue(wizard.summary, feature)
            self.assertIn('<p>', wizard.details)
        driver = self.env['wm.premium.feature.wizard'].create({'feature': 'driver_app'})
        self.assertEqual(driver.module_name, 'wm_driver_app')

    def test_learn_more_actions_open_the_dialog(self):
        for xmlid, feature in (('action_wm_premium_subscription', 'subscription'),
                               ('action_wm_premium_driver_app', 'driver_app')):
            action = self.env.ref('wm_base.' + xmlid)
            self.assertEqual(action.target, 'new')
            self.assertIn(feature, action.context)
