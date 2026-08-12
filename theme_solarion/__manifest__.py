# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#
################################################################################

{
    'name': 'Theme Solarion',
    'version': '17.0.1.0.0',
    'category': 'Theme/Corporate',
    'summary': 'A modern corporate theme',
    'description': 'Solarion Website Theme',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website', 'crm'],
    'data': [
        'security/ir.model.access.csv',
        'data/website_menu_data.xml',
        'views/solarion_product_view.xml',
        'views/layout_view.xml',
        'views/snippets/s_hero_snippet.xml',
        'views/snippets/s_mission_snippet.xml',
        'views/snippets/s_feature_snippet.xml',
        'views/snippets/s_process_snippet.xml',
        'views/snippets/s_product_snippet.xml',
        'views/snippets/s_impact_snippet.xml',
        'views/snippets/s_testimonial_snippet.xml',
        'views/snippets/s_insight_snippet.xml',
        'views/snippets/s_cta_snippet.xml',
        'views/snippets/snippets.xml',
        'views/home_view.xml',
        'views/about_view.xml',
        'views/thankyou_view.xml',
        'views/contact_view.xml',
        'views/impact_view.xml',
        'views/solutions_view.xml',
        'views/technology_view.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'theme_solarion/static/src/scss/style.scss',
            'theme_solarion/static/src/scss/header_features.scss',
            'theme_solarion/static/src/js/main.js',
            'theme_solarion/static/src/js/navbar_interactions.js',
            'theme_solarion/static/src/js/solutions_widget.js',
            'theme_solarion/static/src/js/icon_min.js',
            'theme_solarion/static/src/xml/solutions_widget_templates.xml',
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}

