# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sreeshanth V S (odoo@cybrosys.com)
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
##############################################################################
{
    'name': "Product Nutrition",
    "version": "16.0.1.0.0",
    "category": "eCommerce",
    "summary": "Nutrition and allergen information of products",
    "description": "We can add nutrition ,ingredient and allergen information"
                   "of products on the as product information and can displayed"
                   "on website for website sale",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['product', 'sale', 'website_sale'],
    'data': [
        'security/product_nutrition_allergen_groups.xml',
        'security/ir.model.access.csv',
        'report/product_nutrition_allergen_reports.xml',
        'report/product_nutrition_allergen_templates.xml',
        'views/website_product_template.xml',
        'views/product_template_views.xml'
    ],
    'assets':
        {
            'web.assets_frontend': [
                'product_nutrition_allergen/static/src/js/website_sale.js']
        },
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False
}
