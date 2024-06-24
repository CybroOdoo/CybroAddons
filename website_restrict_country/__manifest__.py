# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ammu Raj (odoo@cybrosys.com)
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
    'name': 'Website Restrict Country',
    'version': '17.0.1.0.0',
    'category': 'Website',
    'summary': "The Website Restrict Country module allows you to set"
               "restrictions for products that are unavailable in certain"
               "countries.",
    'description': "The Website Restrict Country module allows you to set"
                   "restrictions for products that are unavailable in certain"
                   "countries.And You can customise the cart and checkout"
                   "message that is displayed. Customers can select from the"
                   "countries you specify in the Odoo backend.",
    'author': ' Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['stock', 'website_sale', 'sale_stock',
                'sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/website_templates.xml',
        'views/website_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_restrict_country/static/src/js/country_selection.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
