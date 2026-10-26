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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import http
from odoo.http import request


class ProductModel(http.Controller):
    """Provides an endpoint for retrieving AR-related data for a product."""

    @http.route(
        '/product/ar_image',
        type='jsonrpc',
        auth='public',
        website=True,
    )
    def get_product_ar_model(self, product_id, **kwargs):
        """Return AR-related configuration and model URL for a product."""
        try:
            env = request.env if request else kwargs.get('env')
        except RuntimeError:
            env = kwargs.get('env')

        if not env:
            return {}

        try:
            product = env['product.template'].browse(int(product_id))
        except (ValueError, TypeError):
            return {}

        if not product.exists() or not product.enable_ar_images:
            return {}

        # Restrict access to published products unless user is a website editor
        has_designer_rights = env.user.has_group(
            'website.group_website_designer'
        )
        if not product.is_published and not has_designer_rights:
            return {}

        local_url = False
        if product.ar_image_type == 'upload' and product.model_ar:
            filename = product.filename or 'model.glb'
            local_url = (
                f"/web/content/product.template/{product.id}/model_ar/{filename}"
            )

        return {
            'type': product.ar_image_type,
            'ar_url': product.ar_url if product.ar_url else False,
            'ar_scale': product.ar_scale,
            'auto_rotate': product.auto_rotate,
            'ar_placement': product.ar_placement,
            'local_url': local_url,
        }
