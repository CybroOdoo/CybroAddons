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
    'name': 'Theme converza',
    'version': '19.0.1.0.0',
    'category': 'Theme/frontend',
    'summary': 'Design Web Pages with Theme converza',
    'description': 'Theme converza is an ideal choice for your Odoo 18. '
                   'This theme promises to offer a refreshing experience with Odoo, '
                   'enhancing its functionality and aesthetics.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website_blog',
                'website',
                'website_mass_mailing'],
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

        'views/snippets/snippets.xml',
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
            "theme_converza/static/src/css/style.css",
            "theme_converza/static/src/js/main.js",
            'https://code.iconify.design/iconify-icon/1.0.8/iconify-icon.min.js',

        ],
        'website.assets_editor': [
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
