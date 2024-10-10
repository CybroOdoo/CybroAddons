# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: FATHIMA SHALFA P (odoo@cybrosys.com)
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
    'name': "Theme Upshift",
    'version': "17.0.1.0.0",
    'category': 'Theme/Corporate',
    'summary': 'Theme Upshift is a modern and versatile website theme'
    ' designed for businesses looking to establish a professional presence'
    ' and feature',
    'description': 'Theme Upshift is a modern and stylish website template'
    'designed for businesses seeking a dynamic and professional.'
    'It offers a clean, user-friendly layout with customizable sections for'
    'showcasing products, services, and company details.'
    'subtle animations, such as hover effects, fade-ins, and sliding transitions,'
    'enhance the user experience by creating an interactive and engaging interface.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website', 'mail'],
    # data files always loaded at installation
    'data': [
        'data/website_menus.xml',
        'views/about.xml',
        'views/contact_us.xml',
        'views/footer_template.xml',
        'views/header_templates.xml',
        'views/home.xml',
        'views/portfolio_project.xml',
        'views/portfolio_another_action.xml',
        'views/snippet/about_banner.xml',
        'views/snippet/status_section.xml',
        'views/snippet/section_goal.xml',
        'views/snippet/team_section.xml',
        'views/snippet/subscribe_section.xml',
        'views/snippet/home_banner.xml',
        'views/snippet/service_section.xml',
        'views/snippet/process_section.xml',
        'views/snippet/testimonial_section.xml',
        'views/snippet/video_section.xml',
        'views/snippet/location.xml',
        'views/snippet/portfolio_section.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            "https://cdnjs.cloudflare.com/ajax/libs/gsap/3.11.5/gsap.min.js",
            "https://cdnjs.cloudflare.com/ajax/libs/gsap/3.11.5/ScrollTrigger.min.js",
            "https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/TextPlugin.min.js",
            "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js",
            "https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.8/dist/umd/popper.min.js",
            "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.min.js",
            "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css",
            "/theme_upshift/static/src/js/othernavbar.js",
            "/theme_upshift/static/src/css/style.css",
            "/theme_upshift/static/src/js/status_counter.js",
            "/theme_upshift/static/src/css/testimonial_style.css",
        ],
    },
    "images": [
        "static/description/banner.jpg",
        "static/description/theme_screenshot.jpg",
    ],
    "license": "LGPL-3",
    'installable': True,
    'auto_install': False,
    'application': False,
}