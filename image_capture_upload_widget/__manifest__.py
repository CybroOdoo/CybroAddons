# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ranjith R (odoo@cybrosys.com)
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
################################################################################
{
    'name': 'Image Capture Widget',
    'version': '15.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Image Capture Widget for Image Field. '
               'This module allows to capture the users image from the webcam.',
    'description': "This module is used to add Image Capture Widget for Image "
                   "Field. We can capture the image from the webcam and "
                   "upload into the binary field",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/image_capture_views.xml',
    ],
    'assets': {
        'web.assets_qweb': [
            'image_capture_upload_widget/static/src/xml/image_capture_templates.xml',
        ],
        'web.assets_backend': [
            'image_capture_upload_widget/static/src/scss/image_capture.scss',
            'image_capture_upload_widget/static/src/js/image_capture.js',
            'image_capture_upload_widget/static/src/js/image_upload.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
