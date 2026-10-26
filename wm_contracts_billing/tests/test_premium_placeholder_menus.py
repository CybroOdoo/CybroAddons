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
class TestPremiumPlaceholderMenus(TransactionCase):
    """Paid add-ons are visible in the free modules as an information dialog."""

    def test_placeholder_menus_exist(self):
        for xmlid in ('menu_wm_subscription_premium', 'menu_wm_subscription_plan_premium'):
            menu = self.env.ref('wm_contracts_billing.' + xmlid)
            self.assertEqual(menu.parent_id, self.env.ref('wm_contracts_billing.menu_wm_config_customer'))
            self.assertEqual(menu.action._name, 'ir.actions.act_window')
            self.assertEqual(menu.action.res_model, 'wm.premium.feature.wizard')
            self.assertEqual(menu.action.target, 'new')
        installed = self.env['ir.module.module'].search_count(
            [('name', '=', 'wm_subscription'), ('state', '=', 'installed')])
        menu = self.env.ref('wm_contracts_billing.menu_wm_subscription_premium')
        self.assertEqual(menu.active, not installed)

    def test_dialog_content(self):
        for feature in ('subscription', 'subscription_plan'):
            wizard = self.env['wm.premium.feature.wizard'].create({'feature': feature})
            self.assertTrue(wizard.title)
            self.assertTrue(wizard.summary)
            self.assertIn('<p>', wizard.details)

    def test_get_addon_opens_vendor_site(self):
        action = self.env['wm.premium.feature.wizard'].create({}).action_get_addon()
        self.assertEqual(action['type'], 'ir.actions.act_url')
        self.assertTrue(action['url'].startswith('https://'))
