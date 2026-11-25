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

import base64

from odoo import models
from odoo.fields import Domain
from odoo.tools import file_open

# Standard website_sale shop options used by the Petzen shop page
# (same switches as Website > Shop page > Customize in the editor).
PETZEN_SHOP_VIEWS = [
    'website_sale.products_categories',  # category sidebar
    'website_sale.option_collapse_products_categories',
    'website_sale.products_attributes',  # attribute filters
    'website_sale.filter_products_price',  # price filter
    'website_sale.search',  # search box
    'website_sale.sort',  # sorting
    'website_sale.add_grid_or_list_option',  # grid / list switch
    'website_sale.products_add_to_cart',  # "add to cart" on product tiles
]

# Header of the design with Odoo's own header (same switches as the editor's
# Header options): default template with a centered menu, header always visible
# ("Fixed" scroll effect), no text element in the top bar.
PETZEN_HEADER_ENABLE = [
    'website.template_header_default',
    'website.template_header_default_align_center',
    # menu centered like the design
    'website.header_visibility_fixed',
]
PETZEN_HEADER_DISABLE = [
    'website.header_visibility_standard',
    'website.header_visibility_disappears',
    'website.header_visibility_fade_out',
    'website.header_text_element',
    'website.template_header_default_align_right',
]


class ThemeUtils(models.AbstractModel):
    """Website settings applied when the
    Petzen theme is installed on a website."""
    _inherit = 'theme.utils'

    def _theme_petzen_post_copy(self, mod):
        """Called by website when the theme is installed on a website (``mod``
        is the theme module, required by the website hook signature)."""
        self._petzen_enable_shop_views()
        self._petzen_setup_header()

    def _petzen_enable_shop_views(self):
        """Enable the standard shop options used by the Petzen shop page."""
        for xml_id in PETZEN_SHOP_VIEWS:
            if self.env.ref(xml_id, raise_if_not_found=False):
                self.enable_view(xml_id)

    def _petzen_setup_header(self):
        """Select the header options of the design, set the theme logo as
        website logo and the transparent header on the home page."""
        for xml_id in PETZEN_HEADER_DISABLE:
            if self.env.ref(xml_id, raise_if_not_found=False):
                self.disable_view(xml_id)
        for xml_id in PETZEN_HEADER_ENABLE:
            if self.env.ref(xml_id, raise_if_not_found=False):
                self.enable_view(xml_id)
        website = self.env['website'].get_current_website()
        # logo of the design as website logo
        # (Website > Settings / editor: still changeable)
        with file_open(
                'theme_petzen/static/src/images/logo.png', 'rb'
        ) as logo:
            website.logo = base64.b64encode(logo.read())
        # home page: transparent header over the hero
        # (Page > "Header Overlay" in the editor)
        homepage = self.env['website.page'].search(
            Domain.AND([[('url', '=', '/')], website.website_domain()]),
            order='website_id', limit=1)
        if homepage and 'header_overlay' in homepage._fields:
            homepage.header_overlay = True
