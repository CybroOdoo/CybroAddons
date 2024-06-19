# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:Yadhukrishnan K (odoo@cybrosys.com)
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
################################################################################
{
    'name': 'All In One Website Kit',
    'version': '16.0.1.0.0',
    'category': 'Website',
    'summary': """All In One Website for odoo16 community edition to get 
     multiple website feature """,
    'description': """You will get features of the following modules,
     Call for price, customer geolocation, customer order comment, 
     barcode product search, instagram post snippet, portal dashboard,
     cart clear button, custom  contact us form, hide variants, product
     attachment, sale return management and whatsapp floating icon.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'base', 'website_sale_wishlist', 'website_sale_comparison',
        'website_google_map', 'sale_management', 'stock', 'project', 'crm',
        'purchase'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'report/sale_return_reports.xml',
        'report/sale_return_templates.xml',
        'views/shop_hide_call_price_templates.xml',
        'views/wishlist_hide_price_templates.xml',
        'views/compare_hide_price_templates.xml',
        'views/call_for_price_views.xml',
        'views/product_template_views.xml',
        'views/geolocation_portal_templates.xml',
        'views/sale_order_views.xml',
        'views/res_config_settings_views.xml',
        'views/customer_order_comment_templates.xml',
        'views/products_barcode_scan_templates.xml',
        'views/portal_dashboard_templates.xml',
        'views/clear_cart_templates.xml',
        'views/website_views.xml',
        'views/website_contact_us_template.xml',
        'views/product_product_views.xml',
        'views/product_attachments_templates.xml',
        'views/website_thankyou_templates.xml',
        'views/sale_return_views.xml',
        'views/sale_return_templates.xml',
        'views/stock_picking_views.xml',
        'views/insta_post_views.xml',
        'views/insta_profile_views.xml',
        'views/carousal_dashboard_templates.xml',
        'views/portal_whatsapp_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            '/all_in_one_website_kit/static/src/js/create_call_price.js',
            '/all_in_one_website_kit/static/src/js/review_and_rating.js',
            '/all_in_one_website_kit/static/src/css/review_and_rating.css',
            '/all_in_one_website_kit/static/src/js/sale_barcode.js',
            '/all_in_one_website_kit/static/src/js/portal_dashboard_graph.js',
            '/all_in_one_website_kit/static/src/js/variants.js',
            '/all_in_one_website_kit/static/src/js/sale_return.js',
            '/all_in_one_website_kit/static/src/js/caroursel.js',
            'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js',
            '/all_in_one_website_kit/static/src/scss/style.scss',
            '/all_in_one_website_kit/static/src/js/quagga.js',
        ]
    },
    'external_dependencies': {
        'python': ['pytz', 'geopy'],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
