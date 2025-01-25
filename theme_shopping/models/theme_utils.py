# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, models


class ThemeUtils(models.AbstractModel):
    """ Class for enable and disable templates when using theme shopping"""
    _inherit = 'theme.utils'

    @api.model
    def _theme_shopping_post_copy(self, mod):
        """ Enable and disable templates when using coffee shop theme """
        self.enable_view("website_sale.products_categories")
        self.enable_view("website_sale.products_description")
        self.enable_view("website_sale.products_design_card")
        self.enable_view("website_sale.products_add_to_cart")
        self.enable_view("website_sale.product_comment")
        self.enable_view("website_sale.option_collapse_products_categories")
        self.enable_view("website_sale.product_buy_now")
        self.disable_view("website_sale.products_categories_top")
        self.disable_view("website_sale.products_design_grid")
        self.disable_view("website_sale_comparison.add_to_compare")
