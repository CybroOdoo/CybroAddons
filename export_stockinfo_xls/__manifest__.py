# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Midilaj (<https://www.cybrosys.com>)
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
    'name': 'Export Product Stock in Excel',
    'version': '15.0.1.0.0',
    'live_test_url': 'https://www.youtube.com/watch?v=9ae4GkApHQM',
    'summary': "Current Stock Report for all Products in each Warehouse",
    'description': "Current Stock Report for all Products in each Warehouse, Odoo 13,Odoo13",
    'category': 'Warehouse',
    'author': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
                'base',
                'stock',
                'sale',
                'purchase',
                ],
    'data': [
            'views/wizard_view.xml',
            'security/ir.model.access.csv',
            ],
    'images': ['static/description/banner.png'],
    'assets': {
        'web.assets_backend': [
            'export_stockinfo_xls/static/src/js/action_manager.js',
        ],
    },
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'auto_install': False,
}
