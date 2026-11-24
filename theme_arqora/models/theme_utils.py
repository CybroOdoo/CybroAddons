# -*- coding: utf-8 -*-
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models
from odoo.tools import BinaryBytes, file_open

ARQORA_TILE_CLASSES = (
    'o_wsale_products_opt_layout_catalog '
    'o_wsale_products_opt_design_thumbs '
    'o_wsale_products_opt_name_color_regular '
    'o_wsale_products_opt_rounded_0 o_wsale_products_opt_thumb_4_5 '
    'o_wsale_products_opt_thumb_cover o_wsale_products_opt_has_cta '
    'o_wsale_products_opt_actions_inline o_wsale_products_opt_actions_subtle '
    'o_wsale_products_opt_has_wishlist '
    'o_wsale_products_opt_img_secondary_show '
    'o_wsale_products_opt_img_hover_zoom_in_light'
)


class ThemeUtils(models.AbstractModel):
    """Configure the website the way Arqora is designed on theme install."""
    _inherit = 'theme.utils'

    def _theme_arqora_post_copy(self, mod):
        """Set the header, shop and logo defaults of the Arqora design.

        Everything set here stays editable from the website builder. No
        product or category is created: the shop keeps the data of the
        website.
        """
        for xml_id in (
                'website.footer_custom',
                'website_sale.filter_products_price',
                'website_sale.products_categories_list_collapsible',
                'website_sale.products_attributes_collapsible',
        ):
            self.enable_view(xml_id)
        self.enable_view('website.header_visibility_disappears')
        self.disable_view('website.header_visibility_standard')
        for xml_id in (
                'website.header_call_to_action',
                'website.header_text_element',
        ):
            self.disable_view(xml_id)
        website = self.env.website
        with file_open('theme_arqora/static/src/img/logo-dark.png', 'rb') as logo:
            website.logo = BinaryBytes(logo.read())
        with file_open('theme_arqora/static/src/img/favicon.ico', 'rb') as icon:
            website.favicon = BinaryBytes(icon.read())
        website.write({
            'shop_ppr': 3,
            'shop_ppg': 18,
            'shop_gap': '32px',
            'shop_opt_products_design_classes': ARQORA_TILE_CLASSES,
            'wishlist_opt_products_design_classes': ARQORA_TILE_CLASSES,
            'wishlist_grid_columns': 3,
            'wishlist_gap': '32px',
            'prevent_sale': True,
            'prevent_sale_for': 'quote_only',
        })
        self.env['website.page'].search([
            ('url', '=', '/'),
            ('website_id', '=', website.id),
        ]).header_overlay = True
        self._arqora_remove_default_menus(website)

    def _arqora_remove_default_menus(self, website):
        """Remove the default Shop entry that the Collections entry replaces.

        Only an untouched default entry is removed.

        :param website: the website the theme is installed on.
        """
        self.env['website.menu'].search([
            ('website_id', '=', website.id),
            ('parent_id', '=', website.menu_id.id),
            ('theme_template_id', '=', False),
            ('url', '=', '/shop'),
            ('child_id', '=', False),
        ]).unlink()
