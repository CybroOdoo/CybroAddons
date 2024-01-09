# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathti V (odoo@cybrosys.com)
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
import random, werkzeug
from werkzeug.urls import url_encode
from odoo import _, http
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.exceptions import UserError
from odoo.http import _logger, request


class WebsiteLogin(AuthSignupHome):
    """This class used to get the referral code from the website"""

    def web_auth_signup(self, *args, **kw):
        """Overwrite the function web_auth_signup, to add the referral code
        to qcontext"""
        qcontext = self.get_auth_signup_qcontext()
        qcontext.update({
            'referral_code': kw.get('referral_code')
        })
        if not qcontext.get('token') and not qcontext.get('signup_enabled'):
            raise werkzeug.exceptions.NotFound()
        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                self.do_signup(qcontext)
                User = request.env['res.users']
                user_sudo = User.sudo().search(
                    User._get_login_domain(qcontext.get('login')),
                    order=User._get_login_order(), limit=1
                )
                template = request.env.ref(
                    'auth_signup.mail_template_user_signup_account_created',
                    raise_if_not_found=False)
                if user_sudo and template:
                    template.sudo().send_mail(user_sudo.id, force_send=True)
                return self.web_login(*args, **kw)
            except UserError as e:
                qcontext['error'] = e.args[0]
            except (SignupError, AssertionError) as e:
                if request.env["res.users"].sudo().search(
                        [("login", "=", qcontext.get("login"))]):
                    qcontext["error"] = _("Another user is already registered"
                                          " using this email address.")
                else:
                    _logger.error("%s", e)
                    qcontext['error'] = _("Could not create a new account.")
        elif 'signup_email' in qcontext:
            user = request.env['res.users'].sudo().search(
                [('email', '=', qcontext.get('signup_email')),
                 ('state', '!=', 'new')], limit=1)
            if user:
                return request.redirect('/web/login?%s' % url_encode(
                    {'login': user.login, 'redirect': '/web'}))
        response = request.render('auth_signup.signup', qcontext)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
        return response

    def _prepare_signup_values(self, qcontext, **post):
        """Inherited the function _prepare_signup_values to get the current
        referral code and thus want to find partner with that referral code,
         to add points"""
        res = super(WebsiteLogin, self)._prepare_signup_values(qcontext, **post)
        current_referral_code = qcontext.get('referral_code')
        partner_rec = request.env['res.partner'].sudo().search(
            [('referral_code', '=', current_referral_code)])
        if partner_rec:
            signup_points = request.env['ir.config_parameter'].sudo().get_param(
                'refer_friend_and_earn.sign_up_points')
            partner_rec.points = partner_rec.points + float(signup_points)
            partner_rec.sign_up = partner_rec.sign_up + 1
        return res


class ReferAndEarn(http.Controller):
    """This class will allow to generate the referral code and send to
    other person """

    @http.route('/refer/earn', type='http', auth="user", website=True)
    def refer_earn(self):
        """This function is used to create new referral code for newly signup
        one if already logged one is login again, then it will return already
         created referral code"""
        current_user_code = request.env.user.partner_id.referral_code
        if not current_user_code:
            num = "0123456789"
            lowercase = "abcdefghijklmnopqrstuvwxyz"
            capital = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            no_of_digit = 7
            comb = num + lowercase + capital
            codes = "".join(random.sample(comb, no_of_digit))
            request.env.user.partner_id.referral_code = codes
        else:
            codes = request.env.user.partner_id.referral_code
        return request.render('refer_friend_and_earn.refer_earn_template', {
            'codes': codes,
            'points': request.env.user.partner_id.points,
            'sign_up': request.env.user.partner_id.sign_up,
        })

    @http.route('/refer_and_earn/form/submit', type='http', auth="user",
                website=True)
    def refer_and_earn_popup(self, **post):
        """This function will help to collect the recipient of
         mail and send mail to them"""
        base_url = request.env['ir.config_parameter'].sudo().get_param(
            'web.base.url')
        url = '%s/web/signup?' % base_url
        code = post.get('referral_code')
        email_to = post.get('email')
        email_values = {'email_to': email_to,
                        'body_html': '<p>Hello, <br/> Now, its your chance to '
                                     'have unbelivable offers, for that just '
                                     ' click the link %s and use the code %s to'
                                     ' login</p>' % (url, code),
                        }
        login_user = request.env.user.partner_id
        mail_template = request.env.ref(
            'refer_friend_and_earn.mail_template_refer_and_earn')
        mail_template.send_mail(login_user.id, email_values=email_values,
                                force_send=True)
        return request.render('refer_friend_and_earn.website_success_page', {})


class WebsiteSale(WebsiteSale):
    """This class will calculate the discount percentage according to the
     points secured, and also helps to add the discount product in the
     order line"""

    @http.route('/shop/pricelist/points', type='http', auth="user",
                website=True)
    def refer_earn(self, **kw):
        """This function will help to apply the discount according
         to the points  secured"""
        redirect = kw.get('r', '/shop/cart')
        points_rec = request.env['apply.discounts'].sudo().search(
            [('starting_points', '<=', int(kw.get('points'))),
             ('end_points', '>=', int(kw.get('points')))],
            order='create_date desc', limit=1)
        if int(kw.get('points')) > request.env.user.partner_id.points:
            return request.render(
                'refer_friend_and_earn.lack_of_points_template', {})
        if points_rec:
            sale_order = request.website.sale_get_order()
            sale_order.discount_applied = points_rec.discount
            sale_order.points_applied = int(kw.get('points'))
            total_price = sum(sale_order.order_line.mapped('price_subtotal'))
            discount_amount = total_price * (sale_order.discount_applied / 100)
            discount_product_id = request.env['product.product'].sudo().search(
                [('default_code', '=', 'DISCOUNT001')])
            discount_product_id.list_price = -discount_amount
            sale_order.write({'order_line': [(0, 0,
                                              {'id': sale_order.order_line,
                                               'order_id': sale_order,
                                               'product_id': discount_product_id.id,
                                               'product_uom_qty': 1,
                                               })]
                              })
        else:
            return request.render(
                'refer_friend_and_earn.lack_of_points_template', {})
        return request.redirect(redirect)

    @http.route()
    def cart_update_json(self, *args, set_qty=None, **kwargs):
        """This function will work when we have some updates from the cart, ie,
        add or delete the products from the cart"""
        super().cart_update_json(*args, set_qty=set_qty, **kwargs)
        total_price = sum(request.website.sale_get_order().order_line.mapped(
            'price_subtotal'))
        discount_order_line_id = 0
        if total_price <= 0:
            for line in request.website.sale_get_order().order_line:
                line.product_uom_qty = 0
                line.sudo().unlink()
        else:
            discount_product_id = request.env[
                'product.product'].sudo().search(
                [('default_code', '=', 'DISCOUNT001')])
            original_total_price = 0
            for line in request.website.sale_get_order().order_line:
                if line.product_id.id != discount_product_id.id:
                    original_total_price += line.price_subtotal
                else:
                    discount_order_line_id = line.id
            for line in request.website.sale_get_order().order_line:
                if line.product_id.id == discount_product_id.id:
                    discount_percentage = request.website.sale_get_order().discount_applied
                    discount_amount = original_total_price * (
                            discount_percentage / 100)
                    order_line_discount_price = -discount_amount
                    discount_product_id.list_price = -discount_amount
                    order_line = request.website.sale_get_order().order_line.browse(
                        discount_order_line_id)
                    order_line.write({
                        'price_unit': order_line_discount_price,
                    })
        return http.request.redirect(http.request.httprequest.url)

    def shop_payment_confirmation(self, **post):
        """This function is used to decrease the applied points from the
         partner's secured points"""
        sale_order_id = request.session.get('sale_last_order_id')
        res = super().shop_payment_confirmation(**post)
        points = request.env['sale.order'].browse(sale_order_id).points_applied
        request.env.user.partner_id.points = request.env.user.partner_id.points - points
        return res
