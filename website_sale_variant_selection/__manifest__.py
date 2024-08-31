# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Farook Al Ameen (odoo@cybrosys.com)
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
    'name': "Ecommerce Sequential Variant Selector",
    'version': '15.0.1.0.0',
    'category': 'Website',
    'summary': """Sequential attribute selection in odoo eCommerce""",
    'description': "This module enables customers to select product attribute "
                   "values from the website in an ordered manner. It allows "
                   "customers to choose attribute values one by one.",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'website_sale'],
    'data': [
        'views/variant_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_sale_variant_selection/static/src/js/variant_mixin.js',
            'website_sale_variant_selection/static/src/scss/website_sale_attribute_selection.scss',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
