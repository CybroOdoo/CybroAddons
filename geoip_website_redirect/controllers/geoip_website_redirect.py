# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from countryinfo import CountryInfo
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.home import Home


class GeoIP(Home):
    """ controller for selecting login user's datas """
    def get_location(self, ip_address):
        """ Get location details of user using ip address"""
        response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=20).json()
        return {"country": response.get("country")}

    @http.route()
    def web_login(self, redirect=None, **kw):
        """ On login access customer country information """
        result = super().web_login(redirect=redirect, **kw)
        request.env.user.write({'ip_address': kw.get('user_ip')})
        datas = self.get_location(kw.get('user_ip'))
        if datas:
            country = CountryInfo(datas['country'])
            lang = country.languages()
            language = request.env['res.lang'].sudo().search([
                ('iso_code', '=', lang[0]), ('active', 'in', [True, False])])
            if language:
                language.active = True
                request.env['website'].sudo().browse(request.website.id
                                                     ).language_ids = [
                    (4, language.id)]
                url = f'/{language.url_code}'
                return request.redirect(url)
        return result
