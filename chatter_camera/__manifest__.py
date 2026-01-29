# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mruthul Raj (odoo@cybrosys.com)
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
###############################################################################
{
    'name': 'Chatter Camera',
    'version': '15.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Add captured images to the chatter',
    'description': "This module provides an option to capture images directly"
                   " from the chatter and attach them to relevant discussions."
                   "By clicking on the camera button we will have a camera "
                   "screen.We can add captured images to chatter by clicking "
                   "capture button.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['mail'],
    'assets': {
        'web.assets_backend': [
            'chatter_camera/static/src/js/camera_chatter.js',
        ],
        'web.assets_qweb': [
            'chatter_camera/static/src/xml/chatter_camera_templates.xml',
        ]
    },
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
