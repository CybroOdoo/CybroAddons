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
    'name': 'Theme Shopping',
    'version': '20.0.1.0.0',
    'category': 'Theme/eCommerce',
    'summary': 'Responsive eCommerce theme with product deals and testimonials',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': [
        'google_recaptcha', 'mail', 'portal', 'product', 'sale', 'website',
        'website_blog', 'website_mass_mailing', 'website_sale',
    ],
    'data': [
        'security/security_groups.xml',
        'security/ir.access.csv',
        'data/ir_cron.xml',
        'data/product_category_data.xml',
        'views/header_templates.xml',
        'views/footer_templates.xml',
        'views/add_testimonial.xml',
        'views/about_us_views.xml',
        'views/blog_templates.xml',
        'views/snippets/frequently_asked.xml',
        'views/snippets/our_team.xml',
        'views/snippets/new_testimonial_snippet.xml',
        'views/snippets/offers.xml',
        'views/snippets/winter_collections.xml',
        'views/snippets/price_collection.xml',
        'views/snippets/subscription.xml',
        'views/shop_templates.xml',
        'views/snippets.xml',
        'views/product_template_views.xml',
        'views/snippets/top_deal_carousal_templates.xml',
        'views/website_sale_wishlist_template.xml',
        'views/homepage_snippets.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'theme_shopping/static/src/js/carousel.js',
            'theme_shopping/static/src/css/carousel.css',
            "theme_shopping/static/src/js/top_deal_carousel/top_deal_content.xml",
            "theme_shopping/static/src/js/top_deal_carousel/top_deal_carousal.js",
            (
                "theme_shopping/static/src/js/winter_collection_carousel/"
                "winter_products_content.xml"
            ),
            (
                "theme_shopping/static/src/js/winter_collection_carousel/"
                "winter_products_carousel.js"
            ),
            "theme_shopping/static/src/js/snippet_carousel.js",
            "theme_shopping/static/src/js/testimonial.js",
            "theme_shopping/static/src/js/subscription/subscription.js",
            "theme_shopping/static/src/css/main.css",
            "theme_shopping/static/src/css/layout.css",
            "theme_shopping/static/src/js/product_review.js",
        ],
        'web.assets_backend': [
            "theme_shopping/static/src/js/welcome_message.js",
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg',
    ],
    'images_preview_theme': {
        'website.s_cover_default_image': (
            '/theme_shopping/static/description/banner.jpg'
        ),
    },
    'license': 'LGPL-3',
}
