# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: ADVAITH BG (odoo@cybrosys.com)
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
    "name": "Theme LevelUp",
    "version": "17.0.1.0.0",
    "category": "Theme/Corporate",
    "summary": "The perfect website theme for your growing business"
    "can used to apply new design to website and adding more menus "
    "and feature",
    "description": "Introducing Theme LevelUp,"
    " your gateway to the future of web design. "
    "This cutting-edge theme has been meticulously crafted to "
    "transform your website into a captivating online presence."
    " With its breathtaking, visuals, sleek animations, "
    "and modern layouts, Theme LevelUp promises to elevate your "
    "digital identity to new heights. Prepare to amaze your"
    " visitors from the moment they set foot on your home page "
    "and guide them through an immersive web experience like "
    "never before.",
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": ["website", "website_blog"],
    "data": [
        "data/website_menus.xml",
        "views/blog_templates.xml",
        "views/portfolio_templates.xml",
        "views/about_us_templates.xml",
        "views/footer_templates.xml",
        "views/header_templates.xml",
        "views/layout_templates.xml",
        "views/contact_us_templates.xml",
        "views/team_templates.xml",
        "views/service_templates.xml",
        "views/snippets/s_snippet_templates.xml",
        "views/snippets/s_awards_templates.xml",
        "views/snippets/s_service_templates.xml",
        "views/snippets/s_feature_templates.xml",
        "views/snippets/s_excited_templates.xml",
        "views/snippets/s_testimonial_templates.xml",
        "views/snippets/s_client_templates.xml",
        "views/snippets/s_banner_templates.xml",
        "views/snippets/s_about_templates.xml",
        "views/snippets/s_gallery_templates.xml",
        "views/snippets/s_blog_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "theme_levelup/static/src/css/animate.min.css",
            "theme_levelup/static/src/css/owl.carousel.min.css",
            "theme_levelup/static/src/css/owl.theme.default.min.css",
            "theme_levelup/static/src/css/style.css",
            "theme_levelup/static/src/css/font.css",
            "theme_levelup/static/src/css/bootstrap.css",
            "https://cdn.jsdelivr.net/npm/bootstrap@4.0.0/dist/js/"
            "bootstrap.min.js",
            "theme_levelup/static/src/js/index.js",
            "theme_levelup/static/src/js/owl.carousel.js",
            "theme_levelup/static/src/js/owl.carousel.min.js",
            "theme_levelup/static/src/js/service_slider.js",
            "theme_levelup/static/src/js/about_slider.js",
        ],
    },
    "images": [
        "static/description/banner.png",
        "static/description/theme_screenshot.png",
    ],
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
}
