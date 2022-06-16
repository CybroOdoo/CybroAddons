# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Website File Upload',
    'version': '15.0.1.0.0',
    'summary': 'Option To Upload Files In Website',
    'description': 'Option To Upload Files In Website',
    'author': 'Cybrosys Techno solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'license': 'LGPL-3',
    'depends': [
        'website_sale',
        'sale_management',
    ],
    'data': [
        'views/website_sale_templates.xml',
        'views/sale_order_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'assets': {
            'web.assets_frontend': [
                'website_upload_files/static/src/js/attachment.js',
            ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
