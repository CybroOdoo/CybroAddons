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
    'name': 'Theme Cordage',
    'version': '18.0.1.0.0',
    'category': 'Theme/eCommerce',
    'summary': 'Industrial Ropes & Rigging eCommerce Website Theme',
    'description': """
        A complete Odoo 18 eCommerce website theme for industrial rope and
        rigging suppliers. Features dark/light mode, custom cart drawer,
        product filtering, industries showcase, and full website editor support.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website', 'website_sale', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/product_attribute_data.xml',
        # Snippets
        'views/snippets/snippet_groups.xml',
        'views/snippets/s_hero.xml',
        'views/snippets/s_featured_products.xml',
        'views/snippets/s_industries.xml',
        'views/snippets/s_why_choose.xml',
        'views/snippets/s_testimonials.xml',
        'views/snippets/s_quote.xml',
        'views/snippets/s_stats_band.xml',
        'views/snippets/s_about_story.xml',
        'views/snippets/s_team.xml',
        'views/snippets/s_contact_section.xml',
        # Layout (header/footer)
        'views/layout_templates.xml',
        # Backend views
        'views/product_template_views.xml',
        'views/cart_drawer_templates.xml',
        # Website pages
        'views/home_templates.xml',
        'views/industries_templates.xml',
        'views/about_templates.xml',
        'views/contact_templates.xml',
        'views/shop_templates.xml',
        'views/product_templates.xml',
        'views/product_page_override_templates.xml',
        # Website page registrations + navigation menus
        'data/theme_website_menu_data.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            'theme_cordage/static/src/scss/primary_variables.scss',
        ],
        'web.assets_frontend': [
            'theme_cordage/static/src/scss/product_page.scss',
            'theme_cordage/static/src/css/style.css',
            'theme_cordage/static/src/js/data.js',
            'theme_cordage/static/src/js/cordage_cart.js',
            'theme_cordage/static/src/js/cordage_theme.js',
        ],
    },
    'images': [
    	'static/description/banner.jpg',
    	'static/description/theme_screenshot.jpg'
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
