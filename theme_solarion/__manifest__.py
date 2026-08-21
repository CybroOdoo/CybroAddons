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
    'version': '19.0.1.0.0',
    'category': 'Theme/Corporate',
    'summary': 'A modern corporate theme for renewable energy and solar businesses.',
    'description': 'Solarion is a responsive Odoo website theme tailored for solar technology companies, featuring a '
                   'premium dark mode layout and dynamic animations.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website_crm'],
    'data': [
        'security/ir.model.access.csv',
        'views/solarion_product_view.xml',
        'views/layout.xml',
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
        'views/thankyou_template.xml',
        'views/home_template.xml',
        'views/about_template.xml',
        'views/contact_template.xml',
        'views/impact_template.xml',
        'views/solutions_template.xml',
        'views/technology_template.xml',
        'data/website_menu_data.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'theme_solarion/static/src/scss/style.scss',
            'theme_solarion/static/src/js/main.js',
            'theme_solarion/static/src/js/icon.js',
            'theme_solarion/static/src/xml/solutions_widget_templates.xml',
            'theme_solarion/static/src/js/solutions_widget.js',
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
