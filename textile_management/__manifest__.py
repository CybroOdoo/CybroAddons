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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
{
    'name': 'Textile Management',
    'version': '20.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Manage textile products, orders, manufacturing, website inquiries and customer feedback in one app.',
    'description': """
     Manage the textile business in one app: textile products, sale and
     purchase orders, bills of materials and manufacturing orders, with a
     customer and vendor report of the textile orders. On the website,
     visitors send inquiries from a textile inquiry form, managed from the
     backend, and customers rate their order and leave a comment at checkout.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['web', 'mail', 'website', 'stock', 'mrp', 'sale_management',
                'purchase', 'sale_mrp', 'website_sale'],
    'data': [
        'security/ir.access.csv',
        'report/textile_report.xml',
        'report/textile_report_templates.xml',
        'views/inquiry_form_success_templates.xml',
        'views/customer_feedback_templates.xml',
        'views/website_inquiry_views.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'views/mrp_production_views.xml',
        'views/mrp_bom_views.xml',
        'views/textile_management_templates.xml',
        'views/product_template_views.xml',
        'wizard/textile_report_views.xml',
        'views/textile_management_menus.xml',
    ],
    'demo': [
        'demo/textile_demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'textile_management/static/src/fields/**/*',
        ],
        'web.assets_frontend': [
            'textile_management/static/src/interactions/**/*',
            'textile_management/static/src/scss/**/*',
        ],
    },
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'post_init_hook': 'post_init_hook',
}
