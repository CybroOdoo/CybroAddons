# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: ASWIN A K (odoo@cybrosys.com)
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
    'name': 'Dynamic Hover on Related Fields',
    'version': '17.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Dynamic Hover on Related Fields Helps you to '
               'show the configured fields in a tooltip popup',
    'description': 'Enhance your user experience with '
                   'Dynamic Hover on Related Fields! This feature allows '
                   'you to effortlessly display configured fields in '
                   'a convenient tooltip popup. You have the flexibility '
                   'to choose which fields and models you want to showcase '
                   'when hovering over relevant information. '
                   'Simplify your interactions and access key data with ease.',
    'author': 'Cybrosys Techno solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['web'],
    'data': [
        'security/ir.model.access.csv',
        'views/hover_related_fields_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'dynamic_hover_on_related_fields/static/src/xml/*.xml',
            'dynamic_hover_on_related_fields/static/src/js/*.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
