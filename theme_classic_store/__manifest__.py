# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vivek,(odoo@cybrosys.com)
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
    'name': 'Theme Classic Store',
    'version': '16.0.1.0.0',
    'category': 'Theme/eCommerce',
    'summary': 'Theme Classic Store for Odoo Website and e-Commerce',
    'description': 'Theme Classic Store is an attractive eCommerce theme.'
                   'The theme comes with many useful and stylish snippets',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'images': [
        'static/description/banner.png',
        'static/description/theme_screenshot.png',
    ],
    'website': 'https://www.cybrosys.com',
    'depends': ['website_blog', 'website_sale_wishlist',
                'website_sale_comparison'],
    'data': [
        'security/ir.model.access.csv',
        'data/classic_store_config_data.xml',
        'views/classic_store_config_views.xml',
        'views/website_templates.xml',
        'views/website_contactus_templates.xml',
        'views/website_blog_templates.xml',
        'views/http_routing_templates.xml',
        'views/website_sale_templates.xml',
        'views/snippets/snippets_templates.xml',
        'views/snippets/classic_store_aboutus_templates.xml',
        'views/snippets/classic_store_banner_templates.xml',
        'views/snippets/classic_store_categories_templates.xml',
        'views/snippets/classic_store_listing_templates.xml',
        'views/snippets/classic_store_package_templates.xml',
        'views/snippets/classic_store_team_templates.xml',
        'views/snippets/classic_store_counter_templates.xml',
        'views/snippets/classic_store_subheader_templates.xml',
        'views/snippets/classic_store_search_templates.xml',
        'views/snippets/classic_store_trending_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            ('replace', 'website_sale/static/src/js/website_sale_utils.js',
             'theme_classic_store/static/src/js/sale_utils.js'),
            "/theme_classic_store/static/src/css/style.css",
            "/theme_classic_store/static/src/css/style.css.map",
            "/theme_classic_store/static/src/css/animate.min.css",
            "/theme_classic_store/static/src/css/classic_store.css",
            "/theme_classic_store/static/src/css/owl.carousel.min.css",
            "/theme_classic_store/static/src/css/owl.theme.default.min.css",
            "/theme_classic_store/static/src/js/owl.carousel.js",
            "/theme_classic_store/static/src/js/snippets_category.js",
            "/theme_classic_store/static/src/js/snippets_trending.js",
            "/theme_classic_store/static/src/js/shop_sidebar.js",
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
