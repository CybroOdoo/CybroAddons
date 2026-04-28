# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright(C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Aleena K (<https://www.cybrosys.com>)
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
import logging
from werkzeug.exceptions import  NotFound
from odoo import fields, http
from odoo.http import request
from odoo.addons.website.models import ir_http
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website.models.ir_http import sitemap_qs2dom
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.payment.controllers.portal import PaymentPortal


_logger = logging.getLogger(__name__)

class TableCompute(object):
    """
    Class for computing the arrangement of products on a grid.
    """
    def __init__(self):
        self.table = {}

    def _check_place(self, posx, posy, sizex, sizey, ppr):
        """
        Check if a specified rectangular area is available in the table.

        Parameters:
            - posx (int): The starting x-coordinate of the area.
            - posy (int): The starting y-coordinate of the area.
            - sizex (int): The width of the area.
            - sizey (int): The height of the area.
            - ppr (int): Maximum allowed x-coordinate in the table.

        Returns:
            bool: True if the area is available, False otherwise.

        The function iterates over the specified area and checks if each cell is
        within the bounds of the table and if the cell is unoccupied. It returns
        True if the entire area is available; otherwise, it returns False.
        """
        res = True
        for y_area in range(sizey):
            for x_area in range(sizex):
                if posx + x_area >= ppr:
                    res = False
                    break
                row = self.table.setdefault(posy + y_area, {})
                if row.setdefault(posx + x_area) is not None:
                    res = False
                    break
            for x_range in range(ppr):
                self.table[posy + y_area].setdefault(x_range, None)
        return res

    def process(self, products, ppg=20, ppr=4):
        """
        Arrange a list of products on a grid and format the result for HTML
        representation.

        Parameters:
            - products (list): A list of product objects to be arranged on the
            grid.
            - ppg (int): The maximum number of products per grid page
            (default is 20).
            - ppr (int): The maximum number of products per row in the grid
            (default is 4).

        Returns:
            list: A formatted representation of the arranged products suitable
             for HTML rendering.The result is a list of rows, where each row is
             a list of dictionaries representing products and their positions on
             the grid.

        The function iterates over the list of products and computes their
        positions on the grid.It uses a heuristic algorithm to determine the
        position of each product, taking into account the dimensions of the
        products, the maximum products per page, and the maximum products per
        row.The result is formatted as a list of rows, each containing
        dictionaries representing the products and their positions on the grid.
        """
        # Compute products positions on the grid
        minpos = 0
        index = 0
        maxy = 0
        x = 0
        for p in products:
            x = min(max(p.website_size_x, 1), ppr)
            y = min(max(p.website_size_y, 1), ppr)
            if index >= ppg:
                x = y = 1
            pos = minpos
            while not self._check_place(pos % ppr, pos // ppr, x, y, ppr):
                pos += 1
            # if 21st products (index 20) and the last line is full (ppr products in it), break
            # (pos + 1.0) / ppr is the line where the product would be inserted
            # maxy is the number of existing lines
            # + 1.0 is because pos begins at 0, thus pos 20 is actually the 21st block
            # and to force python to not round the division operation
            if index >= ppg and ((pos + 1.0) // ppr) > maxy:
                break

            if x == 1 and y == 1:   # simple heuristic for CPU optimization
                minpos = pos // ppr

            for y2 in range(y):
                for x2 in range(x):
                    self.table[(pos // ppr) + y2][(pos % ppr) + x2] = False
            self.table[pos // ppr][pos % ppr] = {
                'product': p, 'x': x, 'y': y,
                'ribbon': p.sudo().website_ribbon_id,
            }
            if index <= ppg:
                maxy = max(maxy, y + (pos // ppr))
            index += 1

        # Format table according to HTML needs
        rows = sorted(self.table.items())
        rows = [r[1] for r in rows]
        for col in range(len(rows)):
            cols = sorted(rows[col].items())
            x += len(cols)
            rows[col] = [r[1] for r in cols if r[1]]
        return rows


class WebsiteSaleInherit(WebsiteSale):
    """This class inherits from the base WebsiteSale class and includes
    overridden methods and additional functionality for handling sample
    products in the shop,creating sitemap entries for categories, and
    managing the shopping cart."""

    def sitemap_shop(env, rule, qs):
        """This function is overridden to create category.
        Generate sitemap entries for categories in the shop.
           Args:
           env(env): Environment of the function.
           rule: The Sitemap rule object.
           qs (str): Query string parameter.
           Returns:
              yield (dict):Sitemap entries for shop categories."""
        if not qs or qs.lower() in '/shop':
            yield {'loc': '/shop'}
        Category = env['product.public.category']
        dom = sitemap_qs2dom(qs, '/shop/category', Category._rec_name)
        dom += env['website'].get_current_website().website_domain()
        for cat in Category.search(dom):
            loc = '/shop/category/%s' % ir_http._slug(cat)
            if not qs or qs.lower() in loc:
                yield {'loc': loc}

    @http.route([
        '/shop',
        '/shop/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):category>/page/<int:page>',
    ], type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', min_price=0.0,
             max_price=0.0, tags='', **post):
        res = super().shop(
            page=page,
            category=category,
            search=search,
            min_price=min_price,
            max_price=max_price,
            tags=tags,
            **post
        )

        shop_type = post.get('type')
        if not shop_type:
            return res
        website = request.env['website'].get_current_website()
        products = request.env['product.template'].search([
            ('is_sample_product', '=', True),
            ('is_published', '=', True),
        ])
        ppg = res.qcontext['ppg']
        ppr = res.qcontext['ppr']
        gap = res.qcontext['gap']
        layout_mode = res.qcontext['layout_mode']
        variants = request.env['product.product'].sudo().browse(
            p._get_first_possible_variant_id() for p in products
        )
        variants.fetch()
        product_variants = dict(zip(products, variants))
        products_prices = products._get_sales_prices(website)
        res.qcontext.update({
            'products': products,
            'product_variants': product_variants,
            'bins': TableCompute().process(products, ppg, ppr),
            'products_prices': products_prices,
            'get_product_prices': lambda product: products_prices[product.id],
            'ppg': ppg,
            'ppr': ppr,
            'gap': gap,
            'layout_mode': layout_mode,
        })
        return request.render(
            "website_sample_product_request.sample_order_template_view",
            res.qcontext
        )

class CartInherit(PaymentPortal):

    @http.route(route='/shop/cart', type='http', auth="public", website=True,
                    sitemap=False)
    def cart(self, id=None, access_token=None, revive_method='', **post):
        """This function is used to create sample product cart."""
        order = request.cart
        sample_order_line = order.order_line
        for rec in sample_order_line:
            if rec.product_template_id.is_sample_product:
                order.is_sample_order = True
            else:
                order.is_sample_order = False
        if order and order.state != 'draft':
            request.session['sale_order_id'] = None
            order = request.cart
        request.session['website_sale_cart_quantity'] = order.cart_quantity
        values = {}
        if access_token:
            abandoned_order = request.env['sale.order'].sudo().search(
                [('access_token', '=', access_token)], limit=1)
            if not abandoned_order:
                raise NotFound()
            if abandoned_order.state != 'draft':
                values.update({'abandoned_proceed': True})
            elif revive_method == 'squash' or (
                    revive_method == 'merge' and not request.session.get(
                'sale_order_id')):
                request.session['sale_order_id'] = abandoned_order.id
                return request.redirect('/shop/cart')
            elif revive_method == 'merge':
                abandoned_order.order_line.write(
                    {'order_id': request.session['sale_order_id']})
                abandoned_order.action_cancel()
            elif abandoned_order.id != request.session.get(
                    'sale_order_id'):
                values.update({'access_token': abandoned_order.access_token})
        values.update({
            'website_sale_order': order,
            'date': fields.Date.today(),
            'suggested_products': [],
        })
        if order:
            order.order_line.filtered(
                lambda l: not l.product_id.active).unlink()
            values.update(request.website._get_checkout_step_values())
            values.update(self._cart_values(**post))
            values.update(self._prepare_order_history())
            values['suggested_products'] = order._cart_accessories()
            values.update(self._get_express_shop_payment_values(order))
        if post.get('type') == 'popover':
            return request.render("website_sale.cart_popover", values,
                                  headers={'Cache-Control': 'no-cache'})
        return request.render("website_sale.cart", values)
