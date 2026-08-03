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
{
    'name': 'Odoo Web Map',
    'version': '17.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Map View for Odoo Community',
    'description': """
        This module provides a Map View for Odoo Community using Leaflet.
        It allows viewing records on a map based on their latitude and longitude.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'web', 'base_geolocalize'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'wizard/map_view_config_wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_web_map/static/lib/leaflet/leaflet.css',
            'odoo_web_map/static/lib/leaflet/leaflet.js',
            'odoo_web_map/static/src/map_view/map_arch_parser.js',
            'odoo_web_map/static/src/map_view/map_controller.js',
            'odoo_web_map/static/src/map_view/map_model.js',
            'odoo_web_map/static/src/map_view/map_renderer.js',
            'odoo_web_map/static/src/map_view/map_view.js',
            'odoo_web_map/static/src/map_view/map_view.xml',
            'odoo_web_map/static/src/map_view/map_view.scss',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
