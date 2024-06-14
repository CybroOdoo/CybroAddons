# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies(odoo@cybrosys.com)
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
    'name': 'Import Lot from Excel',
    'version': '17.0.1.0.0',
    'category': 'Warehouse',
    'summary': 'Import lots and add while validating a purchase '
               'order picking',
    'description': 'Module helps to import lots and add to products in'
                   'purchase order line while validating a stock_picking ',
    'author': 'Cybrosys Techno Solution',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solution',
    'website': 'https://www.cybrosys.com',
    'depends': ['stock', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_move_views.xml',
        'wizard/lots_attachment_view_form.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'import_lots/static/src/*.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto-install': False,
    'application': False,
}
