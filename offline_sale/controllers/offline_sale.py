# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
################################################################################
import json
import os
from odoo import http
from odoo.http import request
from odoo.modules.module import get_module_path

class OfflineSaleController(http.Controller):
    """HTTP routes for the Offline Sale Progressive Web App."""
    @http.route('/offline_sale/ui', type='http', auth='public')
    def offline_sale_ui(self, **k):
        """Render the main Offline Sale application interface.
        Retrieves Odoo session information and injects it into the
        frontend template so the application can initialize with the
        current user and environment context."""
        try:
            session_info = request.env['ir.http'].session_info()
        except Exception:
            session_info = {}
        return request.render('offline_sale.offline_sale_index', {
            'session_info': session_info,
        })

    @http.route('/offline_sale/sw.js', type='http', auth='public', cors='*')
    def offline_sale_sw(self, **k):
        """Serve the service worker JavaScript file.
        Loads the service worker from the module's static assets and
        returns it with the appropriate headers required for PWA
        functionality and offline caching."""
        module_path = get_module_path('offline_sale')
        if not module_path:
            return request.not_found()
            
        sw_path = os.path.join(module_path, 'static', 'src', 'app', 'sw.js')
        
        if not os.path.exists(sw_path):
            return request.not_found()
            
        with open(sw_path, 'rb') as f:
            content = f.read()
            
        return request.make_response(content, headers=[
            ('Content-Type', 'application/javascript'),
            ('Service-Worker-Allowed', '/offline_sale/'),
        ])

    @http.route('/offline_sale/manifest.json', type='http', auth='public', cors='*', csrf=False)
    def offline_sale_manifest(self, **k):
        """Generate and return the PWA web app manifest.
        Provides metadata such as application name, startup URL,
        theme colors, display mode, and application icons used when
        installing the Offline Sale application on supported devices."""
        manifest = {
            "name": "Offline Sales Terminal V19",
            "short_name": "OfflineSale",
            "description": "Premium Architectural POS Terminal for Odoo 19",
            "start_url": "/offline_sale/ui",
            "display": "standalone",
            "background_color": "#f7faf8",
            "theme_color": "#004f45",
            "icons": [
                {
                    "src": "/offline_sale/static/description/icon.png",
                    "sizes": "512x512",
                    "type": "image/png"
                }
            ]
        }
        return request.make_response(json.dumps(manifest), headers=[('Content-Type', 'application/json')])
