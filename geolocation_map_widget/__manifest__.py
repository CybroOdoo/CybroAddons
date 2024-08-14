# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana K P (odoo@cybrosys.com)
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
    'name': 'GeoLocation Map widget',
    'version': '17.0.1.0.0',
    'category': 'Tools',
    'summary': """The GeoLocation Map widget allows users to obtain the address 
     of the selected location on the map.""",
    'description': """The GeoLocation Map widget enables users to pinpoint 
     a location on the map and retrieve the corresponding address. This feature 
     provides an easy way to identify and display the address of any selected 
     location directly within the map view.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base'],
    'data': [
    ],
    'assets': {
        'web.assets_backend': [
            "https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" ,
            'https://unpkg.com/leaflet@1.7.1/dist/leaflet.js',
            'geolocation_map_widget/static/src/css/goelocation_map.css',
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
