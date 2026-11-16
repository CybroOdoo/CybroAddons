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
from odoo import models

# Standard shop design options of the Voltro product card. They are applied
# once when the theme is installed and stay editable in the website builder.
VOLTRO_TILE_CLASSES = (
    'o_wsale_products_opt_layout_catalog '
    'o_wsale_products_opt_design_cards '
    'o_wsale_products_opt_name_color_regular '
    'o_wsale_products_opt_rounded_4 '
    'o_wsale_products_opt_thumb_cover '
    'o_wsale_products_opt_has_cta '
    'o_wsale_products_opt_actions_inline '
    'o_wsale_products_opt_actions_subtle '
    'o_wsale_products_opt_has_wishlist '
    'o_wsale_products_opt_has_comparison '
    'o_wsale_products_opt_has_rating '
    'o_wsale_products_opt_img_secondary_show '
    'o_wsale_products_opt_img_hover_zoom_in_light '
    'o_wsale_products_opt_cc1'
)


class ThemeUtils(models.AbstractModel):
    """Configure the shop of the website the way Voltro is designed."""
    _inherit = 'theme.utils'

    def _theme_voltro_post_copy(self, mod):
        """Show the shop products as cards with the actions always visible.

        The add to cart, wishlist and comparison buttons stay below the price
        instead of appearing on hover, so they also work on touch screens.
        """
        self.env.website.write({
            'shop_opt_products_design_classes': VOLTRO_TILE_CLASSES,
            'shop_gap': '24px',
        })
