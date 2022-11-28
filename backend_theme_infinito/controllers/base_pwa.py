# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import json
from odoo import http
from odoo.http import request


class BasePwa(http.Controller):
    def pwa_data(self):
        # pwa_enable = request.env[
        #     "ir.config_parameter"].sudo().get_param(
        #     "base_pwa.pwa_enable")
        # if pwa_enable:
        return {
            'short_name': 'Odoo',
            'name': 'Odoo-infinito',
            'description': 'PWA provided by backend theme infinito',
            'icons': [
                {
                    'src': '/backend_theme_infinito/static/src/img/menu.png',
                    'type': 'image/png',
                    'sizes': '144x144',
                    'purpose': 'any maskable'
                },
            ],
            'start_url': 'http://cybrosys:8015/web',
            'background_color': 'white',
            'display': 'standalone',
            'theme_color': 'white',
        }

    @http.route('/manifest/webmanifest', type='http',
                auth='public', website=True, sitemap=False)
    def base_pwa_data(self):
        return request.make_response(json.dumps(self.pwa_data()),
                                     headers=[('Content-Type', 'application/json;charset=utf-8')])
