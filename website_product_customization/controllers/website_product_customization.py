# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Gayathri V @ cybrosys,(odoo@cybrosys.com)
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
#############################################################################
import json
import re
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale.controllers import main


class WebsiteProductCustomization(WebsiteSale):
    """
    Inheriting 'WebsiteSale' class from 'website_sale.controllers.main' to
    modify the method 'cart_update_json'.
    """

    @http.route()
    def cart_update_json(
        self,
        product_id,
        design_image=None,
        line_id=None,
        add_qty=None,
        set_qty=None,
        display=True,
        product_custom_attribute_values=None,
        no_variant_attribute_values=None,
        **kw
    ):
        """
        This route is called :
            - When changing quantity from the cart.
            - When adding a product from the wishlist.
            - When adding a product to cart on the same page
             (without redirection).
        """
        res = super(WebsiteProductCustomization, self).cart_update_json(
            product_id=product_id,
            design_image=design_image,
            line_id=line_id,
            add_qty=add_qty,
            set_qty=set_qty,
            display=display,
            product_custom_attribute_values=product_custom_attribute_values,
            no_variant_attribute_values=no_variant_attribute_values,
            **kw
        )
        order = request.website.sale_get_order(force_create=True)
        if design_image:
            for record in order.order_line:
                if record.id == res["line_id"]:
                    record.product_design = str(
                        re.sub("^data:image\/\w+;base64,", "", design_image),
                    )
                    record.is_customized_product = True
        else:
            if not order.order_line.browse(res["line_id"]).product_design:
                order.order_line.browse(res["line_id"]).product_design = (
                    request.env["product.product"].sudo().browse(product_id).image_1920
                )
        request.session["website_sale_cart_quantity"] = order.cart_quantity
        return res


class WebsiteSale(main.WebsiteSale):
    """
    Inheriting 'WebsiteSale' class from
    'website_sale_product_configurator.controllers.main' to modify the method
    'cart_options_update_json'.
    """

    @http.route()
    def cart_options_update_json(
        self, product_and_options, goto_shop=None, lang=None, **kwargs
    ):
        """This route is called when submitting the optional product modal.
        The product without parent is the main product, the other are options.
        Options need to be linked to their parents with a unique ID.
        The main product is the first product in the list and the options
        need to be right after their parent.
        product_and_options {
            'product_id',
            'product_template_id',
            'quantity',
            'parent_unique_id',
            'unique_id',
            'product_custom_attribute_values',
            'no_variant_attribute_values'
        }
        """
        if lang:
            request.website = request.website.with_context(lang=lang)
        order = request.website.sale_get_order(force_create=True)
        if order.state != "draft":
            request.session["sale_order_id"] = None
            order = request.website.sale_get_order(force_create=True)
        product_and_options = json.loads(product_and_options)
        if product_and_options:
            # The main product is the first, optional products are the rest
            main_product = product_and_options[0]
            design_image = (
                main_product["design_image"] if "design_image" in main_product else None
            )
            value = order._cart_update(
                product_id=main_product["product_id"],
                add_qty=main_product["quantity"],
                product_custom_attribute_values=main_product[
                    "product_custom_attribute_values"
                ],
                no_variant_attribute_values=main_product["no_variant_attribute_values"],
                design_image=design_image,
                **kwargs
            )
            if value["line_id"]:
                # Link option with its parent if line has been created.
                option_parent = {main_product["unique_id"]: value["line_id"]}
                for option in product_and_options[1:]:
                    parent_unique_id = option["parent_unique_id"]
                    option_value = order._cart_update(
                        product_id=option["product_id"],
                        set_qty=option["quantity"],
                        linked_line_id=option_parent[parent_unique_id],
                        product_custom_attribute_values=option[
                            "product_custom_attribute_values"
                        ],
                        no_variant_attribute_values=option[
                            "no_variant_attribute_values"
                        ],
                        design_image=design_image,
                        **kwargs
                    )
                    option_parent[option["unique_id"]] = option_value["line_id"]
                    for record in order.order_line:
                        if record.id == option_value["line_id"]:
                            record.product_design = (
                                request.env["product.product"]
                                .sudo()
                                .browse(option["product_id"])
                                .image_1920
                            )

                if design_image:
                    for record in order.order_line:
                        if record.id == value["line_id"]:
                            record.product_design = str(
                                re.sub(
                                    "^data:image\/\w+;base64,",
                                    "",
                                    main_product["design_image"],
                                ),
                            )
                            record.is_customized_product = True
                else:
                    if not order.order_line.browse(value["line_id"]).product_design:
                        order.order_line.browse(value["line_id"]).product_design = (
                            request.env["product.product"]
                            .sudo()
                            .browse(main_product["product_id"])
                            .image_1920
                        )
        request.session["website_sale_cart_quantity"] = order.cart_quantity
        return str(order.cart_quantity)
