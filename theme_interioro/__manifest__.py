# -*- coding: utf-8 -*-
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Theme Interioro',
    'version': '18.0.1.0.0',
    'category': 'Theme/Corporate',
    'summary': 'Modern Interior Design Website Theme',
    'description': 'Modern Interior Design Website Theme',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website', 'mail'],
    'data': [
        'data/website_menus.xml',
        'security/ir.model.access.csv',
        'data/demo_data.xml',
        'views/interioro_product_views.xml',
        'views/interioro_service_views.xml',
        'views/interioro_menus.xml',
        'views/layout.xml',
        'views/snippet/snippet_groups.xml',
        'views/snippet/breadcrumb_banner.xml',
        'views/snippet/hero_banner.xml',
        'views/snippet/home_intro.xml',
        'views/snippet/about_intro.xml',
        'views/snippet/stats_banner.xml',
        'views/snippet/products_carousel.xml',
        'views/snippet/products_grid.xml',
        'views/snippet/services_grid.xml',
        'views/snippet/interior_types_grid.xml',
        'views/snippet/image_gallery_grid.xml',
        'views/snippet/faq_section.xml',
        'views/snippet/cta_box.xml',
        'views/snippet/contact_form.xml',
        'views/snippet/detail_content_block.xml',
        'views/snippet/brand_strip.xml',
        'views/home.xml',
        'views/about.xml',
        'views/products.xml',
        'views/product_detail.xml',
        'views/services.xml',
        'views/service_detail.xml',
        'views/contact.xml',
        'views/snippet/snippet_options.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'theme_interioro/static/src/scss/style.scss',
            'theme_interioro/static/src/js/theme.js',
        ],
        'website.assets_wysiwyg': [
            'theme_interioro/static/src/js/snippet_options.js',
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
