# -*- coding: utf-8 -*-
import logging
import pprint
import requests
import werkzeug
import json

from openerp import http, SUPERUSER_ID
from openerp.http import request
from openerp.addons.payment.models.payment_acquirer import ValidationError

_logger = logging.getLogger(__name__)

class WepayController(http.Controller):

    @http.route(['/wepay/checkout'], type='http', auth='none', csrf=None, website=True)
    def checkout(self, **post):
        """
        Function which creates the checkout iframe after clicking on PayNow Button. It requires
        wepay account id, and access tocken to create the checkout iframe.
         Check https://developer.wepay.com/api-calls/checkout#create for more Information.
         redirect and the callback_uri must be a full URL and must not include localhost or wepay.com.
         redirect_uri must be a full uri (ex http://www.example.com) if you are in production mode.
        :param post:
        :return: Checkout uri provided after creating checkout, response from /checkout/create
        """
        _logger.info('Wepay datas %s', pprint.pformat(post))  # debug
        cr, uid, context, env = request.cr, SUPERUSER_ID, request.context, request.env
        acquirer = env['payment.acquirer'].sudo().browse(eval(post.get('acquirer')))
        currency = env['res.currency'].sudo().browse(eval(post.get('currency_id'))).name
        if currency not in ['CAD', 'GBP', 'USD']:
            _logger.info("Invalid parameter 'currency' expected one of: 'CAD', 'GBP', 'USD'")
            return request.redirect('/shop/cart')
        url = "https://stage.wepayapi.com/v2/checkout/create" if acquirer.environment == 'test'\
            else "https://wepayapi.com/v2/checkout/create"
        base_url = request.env['ir.config_parameter'].get_param('web.base.url')
        return_url = base_url + '/wepay/checkout/confirm'
        payload = json.dumps({
            "account_id": int(acquirer.wepay_account_id),
            "amount": post.get('amount') or '',
            "type": "goods", #Possible values:, goods, service, donation, event, and personal
            "currency": currency,
            "short_description": "Payment From Odoo E-commerce",
            "long_description": "Payment From Odoo E-commerce",
            "email_message": {
                "to_payer": "Please contact us at 555-555-555 if you need assistance.",
                "to_payee": "Please note that we cover all shipping costs."
            },
            "callback_uri": return_url,#'http://example.com',
            "reference_id": post.get('reference'),
            "auto_release": True,
            "hosted_checkout": {
                "redirect_uri": return_url,
                "shipping_fee": 0,
                "mode": "regular",
                "prefill_info": {
                    "email": post.get('partner_email'),
                    "name": post.get('billing_partner_name') or post.get('partner_name'),
                    "address": {
                        "address1": post.get("billing_partner_address") or '',
                        "address2": post.get("billing_partner_address") or '',
                        "city": post.get('billing_partner_city') or '',
                        "region": post.get("billing_partner_state") or '',
                        "postal_code": post.get('billing_partner_zip') or '',
                        "country": env['res.country'].sudo().browse(eval(post.get("billing_partner_country_id"))).code or ''
                    }
                }
            },
        })
        headers = {
            'content-type': "application/json",
            'authorization': "Bearer %s" % acquirer.wepay_access_tocken.replace(" ", ""),
            'cache-control': "no-cache",
        }
        response = requests.request("POST", url, data=payload, headers=headers)
        vals = json.loads(response.text)
        _logger.info(pprint.pformat(vals))
        return werkzeug.utils.redirect(vals.get('hosted_checkout')['checkout_uri'])

    @http.route(['/wepay/checkout/confirm'], type='http', auth='none', csrf=None, website=True)
    def checkout_confirm(self, **post):
        """
        route which serves when a transaction is completed by wepay through checkout iframe, which we defines the
         return uri while creating wepay checkout. ie, redirect_uri in hosted_checkout dict.
         released,authorized are the successfull transactions and cancelled,falled are the error responses.
        :param post:
        :return: /shop/payment/validate if success else /shop
        """
        cr, uid, context, env = request.cr, SUPERUSER_ID, request.context, request.env
        acquirer = env['payment.acquirer'].sudo().search([('provider', '=', 'wepay')])
        url = "https://stage.wepayapi.com/v2/checkout/" if acquirer and acquirer.environment == 'test' \
            else "https://wepayapi.com/v2/checkout/"
        headers = {
            'content-type': "application/json",
            'authorization': "Bearer %s" % acquirer.wepay_access_tocken.replace(" ", ""),
            'cache-control': "no-cache",
        }
        tx = request.website.sale_get_transaction()
        tx.sudo().wepay_checkout_id = post.get('checkout_id')
        response = requests.request("POST", url, data=json.dumps(post), headers=headers)
        vals = json.loads(response.text)
        _logger.info(pprint.pformat(vals))
        if vals.get('state') == 'authorized':
            tx.state = 'done'
            tx.wepay_checkout_id = vals.get('checkout_id')
            tx.sale_order_id.with_context(dict(context, send_email=True)).action_confirm()
            return request.redirect('/shop/payment/validate')
        elif vals.get('state') in ['cancelled', 'falled']:
            tx.state = 'error'
            return request.redirect('/shop')
        elif vals.get('state') in ['released']:
            tx.state = 'pending'
            tx.wepay_checkout_id = vals.get('checkout_id')
            tx.sale_order_id.with_context(dict(context, send_email=True)).action_confirm()
            return request.redirect('/shop/payment/validate')


