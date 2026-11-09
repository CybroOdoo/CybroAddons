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
#############################################################################
{
    'name': 'Geolocation Map Widget',
    'version': '20.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Geolocation map widget that allows users to retrieve address from selected map location',
    'description': """The Geolocation Map widget enables users to pinpoint a location on the map and 
    retrieve the corresponding address. This feature provides an easy way to identify and display the
    address of any selected location directly within the map view.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'web'],
    'assets': {
        'web.assets_backend': [
            'geolocation_map_widget/static/lib/leaflet/leaflet.css',
            'geolocation_map_widget/static/src/css/geolocation_map.css',
            'geolocation_map_widget/static/src/js/geolocation_map.js',
            'geolocation_map_widget/static/src/xml/geolocation_map_templates.xml',
        ],
        'web.assets_unit_tests': [
            'geolocation_map_widget/static/lib/leaflet/leaflet.js',
            'geolocation_map_widget/static/lib/leaflet/leaflet.css',
            'geolocation_map_widget/static/src/**/*',
            'geolocation_map_widget/static/tests/**/*',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
