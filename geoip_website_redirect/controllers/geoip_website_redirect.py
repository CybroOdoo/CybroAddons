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
import requests
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.home import Home


class Geolocation(Home):
    """ controller for selecting login user's datas """

    def get_location(self, ip_address):
        """ Get location details of user using ip address"""
        try:
            response = requests.get(f'http://ip-api.com/json/{ip_address}',
                                    timeout=20).json()
            return {"country": response.get("country")}
        except:
            return {}

    @http.route()
    def web_login(self, redirect=None, **kw):
        """ On login access customer country information """
        user_ip = kw.get('user_ip')
        if user_ip:
            request.session['user_ip'] = user_ip
        result = super().web_login(redirect=redirect, **kw)
        if request.session.uid:
            user = request.env.user.sudo()
            user.write({'ip_address': user_ip})
            datas = self.get_location(user_ip)
            if datas and datas.get('country'):
                try:
                    from countryinfo import CountryInfo
                    country = CountryInfo(datas['country'])
                    lang = country.languages()
                    if lang:
                        language = request.env['res.lang'].sudo().search([
                            ('iso_code', '=', lang[0]),
                            ('active', 'in', [True, False])
                        ], limit=1)

                        if language:
                            language.sudo().write({'active': True})
                            website = request.env['website'].sudo().browse(request.website.id)
                            website.sudo().write({
                                'language_ids': [(4, language.id)]
                            })
                            user.sudo().write({
                                'lang': language.code
                            })
                            request.session['context'] = dict(request.session.get('context', {}))
                            request.session['context']['lang'] = language.code
                            currencies = country.currencies()
                            if currencies:
                                currency = request.env['res.currency'].sudo().search([
                                    ('name', '=', currencies[0]),
                                    ('active', 'in', [True, False])
                                ], limit=1)
                                if currency:
                                    currency.sudo().write({'active': True})
                            url = f'/{language.url_code}'
                            return request.redirect(url)
                except Exception as e:
                    import logging
                    _logger = logging.getLogger(__name__)
                    _logger.warning(f"Error setting language: {e}")
        return result
