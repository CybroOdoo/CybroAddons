# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anjhana A K (odoo@cybrosys.com)
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
    'name': 'Login using QR Code',
    'version': '16.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Users can login by scanning QR Code',
    'description': 'A QR code is generate corresponding to each internal user'
                   ' and,they can use this QR code to login to their account by'
                   ' scanning it',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'http://www.cybrosys.com',
    'data': [
        'views/login_templates.xml',
        'views/res_users_views.xml',
        'views/login_using_qr_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'login_using_qr/static/src/js/login_with_qr.js',
            'login_using_qr/static/src/css/login_with_qr.css',
            'https://cdn.rawgit.com/cozmo/jsQR/master/dist/jsQR.js',
           ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
