# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K (odoo@cybrosys.com)
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
##############################################################################
{
    'name': "Water Supply With Manufacturing Order",
    'version': '17.0.1.0.0',
    'category': 'Manufacturing',
    'summary': """This app allows you to create water supplying methods""",
    'description': """This app allows you to create water supplying methods
     allows us to create manufacture orders from water supply requests.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['account', 'mail', 'mrp'],
    'data': [
        'security/water_supply_with_mo_groups.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/water_supply_method_views.xml',
        'views/water_usage_places_views.xml',
        'views/water_usage_categories_views.xml',
        'views/water_supply_request_views.xml',
        'views/manufacturing_order_creation_views.xml',
        'views/mrp_production_views.xml',
        'views/water_supply_with_mo_menus.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
