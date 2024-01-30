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
    'name': 'Image Capture Widget',
    'version': '17.0.1.0.0',
    'category': 'Extra Tools',
    'sequence': '20',
    'summary': 'Image Capture Widget for Image Field. '
               'This module allows to capture the users image from the webcam.',
    'author': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'description': "This module is used to add Image Capture Widget for Image "
                   "Field. We can capture the image from the webcam and "
                   "upload into the binary field",
    'depends': ['sale_management', 'contacts'],
    'images': ['static/description/banner.jpg'],
    'data': [
        'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_backend': [
            '/image_capture_upload_widget/static/src/scss/image_capture.scss',
            '/image_capture_upload_widget/static/src/js/image_capture.js',
            '/image_capture_upload_widget/static/src/xml/image_capture_templates.xml',
        ],
    },
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
