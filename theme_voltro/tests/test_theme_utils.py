################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo.tests import tagged

from odoo.addons.theme_voltro.models.theme_utils import VOLTRO_TILE_CLASSES
from odoo.addons.website_sale.tests.common import WebsiteSaleCommon


@tagged('post_install', '-at_install')
class TestThemeUtils(WebsiteSaleCommon):
    """Test the shop design set when the theme is applied."""

    def test_shop_design_on_theme_load(self):
        """Applying the theme sets the card design and the grid gap."""
        theme = self.env['ir.module.module'].with_context(
            apply_new_theme=True).with_user(
            self.env.ref('base.user_admin')).search(
            [('name', '=', 'theme_voltro')], limit=1)
        theme._theme_load(self.website)
        self.assertEqual(
            self.website.shop_opt_products_design_classes, VOLTRO_TILE_CLASSES)
        self.assertEqual(self.website.shop_gap, '24px')

    def test_design_keeps_the_actions_visible(self):
        """The card design uses standard options with the actions inline."""
        classes = VOLTRO_TILE_CLASSES.split()
        self.assertIn('o_wsale_products_opt_design_cards', classes)
        self.assertIn('o_wsale_products_opt_actions_inline', classes)
        self.assertNotIn('o_wsale_products_opt_actions_onhover', classes)
