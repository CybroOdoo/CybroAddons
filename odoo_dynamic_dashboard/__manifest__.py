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
    'name': "AI Dynamic Dashboard Pro",
    'version': '19.0.2.0.0',
    'category': 'Productivity',
    'summary': 'AI-powered drag-and-drop dashboard builder for Odoo. '
               'Charts, KPIs, tables, themes and smart insights in one place.',
    'description': 'Build interactive, responsive dashboards with a drag-and-drop grid layout. '
                   'Add cards for charts, KPI blocks, tables, to-do lists, embedded views and '
                   'activities, then group and filter them by date or custom domains. Includes '
                   'AI-assisted card generation and per-card business insights (Google Gemini or '
                   'Odoo AI), customizable themes with company-logo palette extraction, and '
                   'reusable color groups.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['web','hr','web_hierarchy','hr_org_chart'],
    'external_dependencies': {
        'python': ['google-genai'],
    },
    'data': [
        'security/dashboard_security.xml',
        'security/dashboard_security_data.xml',
        'security/ir.model.access.csv',
        'views/dashboard_views.xml',
        'views/dashboard_menu_views.xml',
        'views/dashboard_card_views.xml',
        'views/dashboard_wizard_views.xml',
        'views/dashboard_color_group_views.xml',
        'views/add_to_dashboard_wizard.xml',
        'views/dashboard_theme_group_views.xml',
        'views/res_config_settings_views.xml',
        'data/dashboard_color_data.xml',
        'data/dashboard_theme_data.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_dynamic_dashboard/static/src/lib/gridstack/dist/gridstack.min.css',
            'odoo_dynamic_dashboard/static/src/lib/apexcharts/dist/apexcharts.min.js',
            'odoo_dynamic_dashboard/static/src/lib/gridstack/dist/gridstack-all.js',
            'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css',
            # Restructured assets
            'odoo_dynamic_dashboard/static/src/js/**/*.js',
            'odoo_dynamic_dashboard/static/src/xml/**/*.xml',
            'odoo_dynamic_dashboard/static/src/css/**/*.css',
            'odoo_dynamic_dashboard/static/src/css/**/*.scss',

            'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js',
            'https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': "AGPL-3",
    'installable': True,
    'auto_install': False,
    'application': True,
}
