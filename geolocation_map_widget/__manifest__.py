# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################
{
    'name': 'Geolocation Map Widget',
    'version': '18.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Geolocation map widget that allows users to retrieve address from selected map location',
    'description': """The Geolocation Map widget enables users to pinpoint a location on the map and 
    retrieve the corresponding address. This feature provides an easy way to identify and display the
    address of any selected location directly within the map view.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base'],
    'assets': {
        'web.assets_backend': [
            "https://unpkg.com/leaflet@1.7.1/dist/leaflet.css",
            'https://unpkg.com/leaflet@1.7.1/dist/leaflet.js',
            'geolocation_map_widget/static/src/css/geolocation_map.css',
            'geolocation_map_widget/static/src/js/geolocation_map.js',
            'geolocation_map_widget/static/src/xml/geolocation_map_templates.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
