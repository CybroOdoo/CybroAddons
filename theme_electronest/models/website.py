# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
from odoo import api, fields, models
from odoo.http import request


class Website(models.Model):
    """ Inherited and added the shop product layout field"""
    _inherit = 'website'

    shop_product_layout = fields.Selection(
        selection=[('list', 'List'), ('grid', 'Grid')],
        string='Shop Product Layout',
        default='grid',
    )

    @api.model
    def set_shop_product_layout(self, layout):
        """ Function set the layout class based on the event"""
        website = request.env['website'].get_current_website()
        if layout == 'list':
            write_vals = {
                'shop_opt_products_design_classes': 'o_wsale_products_opt_name_color_regular o_wsale_products_opt_thumb_cover o_wsale_products_opt_has_cta o_wsale_products_opt_has_wishlist o_wsale_products_opt_actions_inline o_wsale_products_opt_cc o_wsale_products_opt_cc1 o_wsale_products_opt_rounded_1 o_wsale_products_opt_actions_promote o_wsale_products_opt_name_size_body o_wsale_products_opt_layout_list o_wsale_products_opt_design_condensed',
                'shop_gap': '4px',
            }
        else:
            write_vals = {
                'shop_opt_products_design_classes': 'o_wsale_products_opt_name_color_regular o_wsale_products_opt_thumb_cover o_wsale_products_opt_img_secondary_show o_wsale_products_opt_img_hover_zoom_out_light o_wsale_products_opt_has_cta o_wsale_products_opt_has_wishlist o_wsale_products_opt_has_comparison o_wsale_products_opt_actions_onhover o_wsale_products_opt_wishlist_fixed o_wsale_products_opt_actions_subtle o_wsale_products_opt_thumb_4_3 o_wsale_products_opt_layout_catalog o_wsale_products_opt_design_grid',
                'shop_gap': '0px',
            }
            layout = 'grid'
        write_vals['shop_product_layout'] = layout
        website.write(write_vals)
        return True

    @api.model
    def get_shop_product_layout(self):
        """ get the current website shop product layout """
        website = request.env['website'].get_current_website()
        return website.shop_product_layout or 'grid'
