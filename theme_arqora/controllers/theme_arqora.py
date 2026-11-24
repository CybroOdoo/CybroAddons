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
from odoo.exceptions import UserError
from odoo.http import Controller, request, route

from odoo.addons.website_sale.controllers.wishlist import ProductWishlist


class ArqoraStore(Controller):
    """Serve the dynamic blocks of the Arqora home page.

    Only the presentation lives here: categories, products and prices are
    the eCommerce records of the website.
    """

    @route('/theme_arqora/collections', type='jsonrpc', auth='public',
           website=True, sitemap=False, readonly=True)
    def collections(self, limit=6):
        """Render the lamp tiles of the Collections block.

        :param int limit: the maximum number of tiles.
        :return: the markup of the tiles.
        :rtype: dict
        """
        limit = max(1, min(int(limit or 6), 12))
        return {'html': request.env['ir.ui.view']._render_template(
            'theme_arqora.collection_tiles', {
                'collections': request.env.website._arqora_collections(limit),
            })}

    @route('/theme_arqora/signature', type='jsonrpc', auth='public',
           website=True, sitemap=False, readonly=True)
    def signature(self, limit=5):
        """Render the cards of the Objects of Light mosaic.

        :param int limit: the maximum number of cards.
        :return: the markup of the cards.
        :rtype: dict
        """
        limit = max(1, min(int(limit or 5), 9))
        return {'html': request.env['ir.ui.view']._render_template(
            'theme_arqora.signature_cards', {
                'products': request.env.website._arqora_signature(limit),
            })}

    @route('/theme_arqora/quote_product', type='jsonrpc', auth='public',
           website=True, sitemap=False, readonly=True)
    def quote_product(self, product_id):
        """Describe the product of a quotation for the enquiry form.

        :param int product_id: the id of the product.template.
        :return: the name, family, image and price, or an empty dict.
        :rtype: dict
        """
        website = request.env.website
        product = request.env['product.template'].browse(
            int(product_id or 0)).exists()
        if not product or not product.sudo()._is_published():
            return {}
        return {
            'name': product.name,
            'family': ', '.join(product.public_categ_ids.mapped('name')),
            'image': '/web/image/product.template/{}/image_512'.format(
                product.id),
            'price': website._arqora_price(product._get_contextual_price()),
        }


class ArqoraWishlist(ProductWishlist):
    """Keep the products sold on quotation out of the wishlist."""

    @route()
    def add_to_wishlist(self, product_id, **kwargs):
        """Refuse a product marked Request a Quote.

        :param int product_id: the product.product to add.
        :raise UserError: when the product is sold on quotation only.
        """
        product = request.env['product.product'].browse(product_id).exists()
        if product and request.env.website._arqora_is_quote_only(product):
            raise UserError(request.env._(
                'This product is sold on quotation. Please request a quote.'))
        return super().add_to_wishlist(product_id, **kwargs)
