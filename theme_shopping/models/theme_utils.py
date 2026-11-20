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
from odoo import api, models


class ThemeUtils(models.AbstractModel):
    """ Class for enable and disable templates when using theme shopping"""
    _inherit = 'theme.utils'

    @api.model
    def _theme_shopping_post_copy(self, mod):
        """Enable the shop options used by Theme Shopping."""
        self.enable_view("website_sale.products_categories")
        self.enable_view("website_sale.product_comment")
        self.enable_view("website_sale.option_collapse_products_categories")
        self.enable_view("website_sale.product_buy_now")
        self.disable_view("website_sale.products_categories_top")
        self.disable_view("website_sale.add_to_compare")
