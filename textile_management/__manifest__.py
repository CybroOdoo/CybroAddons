# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

{
    'name': 'Textile Management',
    'version': '19.0.1.0.0',
    'category': 'Extra Tools',
    'summary': "To manage Textile Industry",
    'description': """To manage textile industry process such as purchase of 
    raw materials, manufacture the product and sale the final product""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale_management', 'purchase', 'stock', 'mail', 'mrp',
                'website_sale', 'sale_mrp'],
    'data': [
        'security/ir.model.access.csv',
        'views/inquiry_form_success_templates.xml',
        'views/customer_feedback_templates.xml',
        'views/textile_management_menus.xml',
        'views/website_inquiry_views.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'views/mrp_production_views.xml',
        'views/mrp_bom_views.xml',
        'views/textile_management_templates.xml',
        'views/product_template_views.xml',
        'report/textile_report.xml',
        'report/textile_report_templates.xml',
        'wizard/textile_report_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'textile_management/static/src/js/review_and_rating.js',
            'textile_management/static/src/css/review_and_rating.css'
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
    'post_init_hook': 'post_init_hook',
}
