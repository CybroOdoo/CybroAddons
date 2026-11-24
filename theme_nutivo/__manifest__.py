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
#############################################################################
{
    'name': 'Theme Nutivo',
    'version': '20.0.1.0.0',
    'category': 'Theme/eCommerce',
    'summary': 'A refined eCommerce theme for premium nuts, dates, dried '
               'fruits and gift hampers.',
    'description': 'Theme Nutivo gives a gourmet dry-fruit brand a complete '
                   'online store: an ivory, forest green and gold design with '
                   'an announcement bar, a Shop mega menu, home, our story and '
                   'contact pages built from editable snippets, smooth '
                   'scrolling and scroll animations. Product cards offer the '
                   'pack sizes of each product; the shop has price, rating and '
                   'highlight filters, and the bag and wishlist drawers, '
                   'search and quick view use the standard eCommerce data.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website_sale', 'website_mass_mailing'],
    'data': [
        'views/snippets/s_nutivo_hero.xml',
        'views/snippets/s_nutivo_ticker.xml',
        'views/snippets/s_nutivo_categories.xml',
        'views/snippets/s_nutivo_goodness.xml',
        'views/snippets/s_nutivo_bestsellers.xml',
        'views/snippets/s_nutivo_hampers.xml',
        'views/snippets/s_nutivo_festive.xml',
        'views/snippets/s_nutivo_testimonials.xml',
        'views/snippets/s_nutivo_newsletter.xml',
        'views/snippets/s_nutivo_page_hero.xml',
        'views/snippets/s_nutivo_about_intro.xml',
        'views/snippets/s_nutivo_stats.xml',
        'views/snippets/s_nutivo_timeline.xml',
        'views/snippets/s_nutivo_process.xml',
        'views/snippets/s_nutivo_origins.xml',
        'views/snippets/s_nutivo_founder.xml',
        'views/snippets/s_nutivo_cta.xml',
        'views/snippets/s_nutivo_help.xml',
        'views/snippets/s_nutivo_faq.xml',
        'views/snippets/s_nutivo_perks.xml',
        'views/snippets/s_nutivo_contact.xml',
        'views/snippets/snippets.xml',
        'views/layout_templates.xml',
        'views/header_templates.xml',
        'views/store_templates.xml',
        'views/home_templates.xml',
        'views/about_templates.xml',
        'views/contact_templates.xml',
        'views/shop_templates.xml',
        'views/checkout_templates.xml',
        'data/website_menu_data.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            'theme_nutivo/static/src/scss/primary_variables.scss',
        ],
        'web.assets_frontend': [
            'theme_nutivo/static/lib/gsap/gsap.min.js',
            'theme_nutivo/static/lib/gsap/ScrollTrigger.min.js',
            'theme_nutivo/static/lib/lenis/lenis.min.js',
            'theme_nutivo/static/src/scss/fonts.scss',
            'theme_nutivo/static/src/scss/icons.scss',
            'theme_nutivo/static/src/scss/nutivo.scss',
            'theme_nutivo/static/src/scss/odoo_overrides.scss',
            'theme_nutivo/static/src/scss/shop.scss',
            'theme_nutivo/static/src/scss/header.scss',
            'theme_nutivo/static/src/js/nutivo_store.js',
            'theme_nutivo/static/src/js/nutivo_motion.js',
            'theme_nutivo/static/src/js/nutivo_snippets.js',
        ],
        'website.website_builder_assets': [
            'theme_nutivo/static/src/js/builder/nutivo_builder_plugin.js',
            'theme_nutivo/static/src/xml/builder/nutivo_options.xml',
        ],
        'website.assets_inside_builder_iframe': [
            'theme_nutivo/static/src/scss/edit_mode.edit.scss',
        ],
        'html_builder.iframe_add_dialog': [
            'theme_nutivo/static/src/scss/edit_mode.edit.scss',
        ],
    },
    'license': 'LGPL-3',
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
