# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys (<https://www.cybrosys.com>)
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
    'name': 'Theme Converza',
    'version': '17.0.1.0.0',
    'category': 'Theme/Corporate',
    'summary': 'Digital marketing agency theme for Odoo 17 websites',
    'description': 'Theme Converza is a modern, fully responsive website '
                   'theme for digital marketing agencies. It ships ready-made '
                   'pages (services, results, case studies, pricing, about us, '
                   'contact), website builder snippets, a custom header and '
                   'footer, and a redesigned blog.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website', 'website_blog', 'website_mass_mailing'],
    'data': [
        'data/menu_data.xml',
        'views/header_templates.xml',
        'views/footer_templates.xml',
        'views/home_page.xml',
        'views/service_page.xml',
        'views/case_study_page.xml',
        'views/result_page.xml',
        'views/pricing_page.xml',
        'views/blog_page.xml',
        'views/about_us_page.xml',
        'views/contact_us.xml',
        'views/snippets/s_service_templates.xml',
        'views/snippets/s_marketing_snippets.xml',
        'views/snippets/s_about_template.xml',
        'views/snippets/s_result_analytics.xml',
        'views/snippets/s_process_template.xml',
        'views/snippets/s_pricing_template.xml',
        'views/snippets/s_testimonials_template.xml',
        'views/snippets/s_case_study_template.xml',
        'views/snippets/s_team_template.xml',
        'views/snippets/s_insights_template.xml',
        'views/snippets/s_contact_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'theme_converza/static/lib/iconify/iconify-icon.min.js',
            'theme_converza/static/src/css/style.css',
            'theme_converza/static/src/js/main.js',
        ],
        'web.assets_tests': [
            'theme_converza/static/tests/tours/*.js',
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
