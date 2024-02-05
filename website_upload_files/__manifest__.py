# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathti V (odoo@cybrosys.com)
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
    'name': 'Multiple Attachments In eCommerce Order',
    'version': '17.0.1.0.0',
    'category': 'eCommerce',
    'summary': 'Can upload files in payment page of website.',
    'description': 'Can upload files related to the sale order in payment page'
                   'of website.This attachment can also view in website order.'
                   'Through the attachment we can give further details or '
                   'information regarding the sale order.',
    'author': 'Cybrosys Techno solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'website_sale', 'sale_management',
    ],
    'data': [
        'views/website_sale_templates.xml',
        'views/sale_order_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_upload_files/static/src/js/attachment.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
