#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
{
    'name': 'Top Selling Products In Category',
    'version': '20.0.1.0.0',
    'category': 'eCommerce',
    'summary': 'Showcase Top Selling Products by Category on Website',
    'description': 'Showcase best-selling products on your website categorized '
                   'by eCommerce product category. If multiple products exist, '
                   'a slider carousel is displayed for each category. A "View All" '
                   'button links directly to the category shop page.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website_sale'],
    'data': [
        'views/product_breadcrumb_templates.xml',
        'views/top_products_category_wise_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'top_selling_products_in_category/static/src/js/top_selling_products.js',
            'top_selling_products_in_category/static/src/xml/top_products_templates.xml',
            'top_selling_products_in_category/static/src/css/products_carousel.css',
        ],
        'web.assets_unit_tests': [
            'top_selling_products_in_category/static/tests/**/*',
        ],
        'web.assets_unit_tests_setup': [
            'top_selling_products_in_category/static/src/**/*',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
