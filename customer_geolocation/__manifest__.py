# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
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
#############################################################################
{
    'name': "Customer Geolocation In Website",
    'version': '16.0.1.0.0   ',
    'depends': ['base', 'website', 'website_google_map', 'portal'],
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'images': ['static/description/banner.png'],
    'website': 'https://www.cybrosys.com',
    'category': 'Website',
    'description': "This helps customer to add their address through map and locate the address",
    'summary': 'Geolocation In website. '
               'This helps customer to add their address through map and locate the address.',
    'assets': {
        'web.assets_frontend': [
            'customer_geolocation/static/src/css/cust_geolocation.css',
        ],
    },
    'data': [
        'views/portal_templates.xml',
    ],
    'external_dependencies': {
        'python': ['pytz', 'geopy'],
    },

    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
