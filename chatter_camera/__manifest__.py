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
    'name': 'Chatter Camera',
    'version': '20.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Camera on Chatter',
    'description': 'Capture images from the chatter and attach them directly '
                   'to records in Odoo 20',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['mail'],
    'assets': {
        'web.assets_backend': [
            'chatter_camera/static/src/css/style.css',
            'chatter_camera/static/src/js/chatter_camera.js',
            'chatter_camera/static/src/xml/chatter_camera.xml',
        ],
        'web.assets_unit_tests': [
            'chatter_camera/static/tests/**/*',
            ('remove', 'chatter_camera/static/tests/tours/**/*'),
        ],
        'web.assets_tests': [
            'chatter_camera/static/tests/tours/**/*',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
