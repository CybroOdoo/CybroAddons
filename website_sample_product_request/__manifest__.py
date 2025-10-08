# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright(C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Rosmy John (<https://www.cybrosys.com>)
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
#############################################################################
{
    'name': 'Website Sample Product Request',
    'version': '16.0.1.0.0',
    'category': 'Website',
    'summary': 'This module allows us to create sample request from website,'
               'in odoo 16',
    'description': 'This module allows us to create sample request from website'
                   'by choosing sample product from backend,odoo 16',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['sale_management', 'website_sale'],
    'data': [
        'data/website_menu_data.xml',
        'views/product_product_views.xml',
        'views/product_template_views.xml',
        'views/website_sample_product_templates.xml',
        'views/sale_order_views.xml',
        'views/website_sample_product_request_menus.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
