# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Waste Management Base',
    'version': '19.0.1.0.0',
    'category': 'Operations/Waste Management',
    'summary': 'Base module for Waste Management',
    'description': "Provides core models, configurations, and electronic signature utilities for Waste Management.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Technologies Pvt. Ltd.',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'base',
        'mail',
        'product',
        'web',
        'portal',
    ],
    'external_dependencies': {
        'python': ['PyPDF2', 'reportlab', 'PIL'],
    },
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/waste_category_data.xml',
        'data/waste_material_data.xml',
        'data/wm_signature_sequence_data.xml',
        'data/wm_signature_mail_template_data.xml',
        'wizards/wm_signature_request_wizard_views.xml',
        'wizards/wm_signature_sign_now_wizard_views.xml',
        'views/res_config_settings_views.xml',
        'views/webclient_login_templates.xml',
        'views/wm_dashboard_views.xml',
        'views/menu_views.xml',
        'views/wm_audit_log_views.xml',
        'views/product_template_views.xml',
        'views/wm_waste_category_views.xml',
        'views/wm_waste_material_views.xml',
        'views/wm_container_type_views.xml',
        'views/wm_compliance_code_views.xml',
        'views/wm_signature_role_views.xml',
        'views/wm_signature_template_views.xml',
        'views/wm_signature_request_views.xml',
        'views/wm_signature_portal_templates.xml',
        'views/sign_now_views.xml',
        'reports/wm_signature_report.xml',
        'reports/wm_signature_report_templates.xml',
        'views/wm_signature_menu_views.xml',
    ],
    'demo': [
        'demo/demo_waste_data.xml',
        'demo/demo_signature_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'wm_base/static/src/css/signature_portal.css',
            'wm_base/static/src/scss/portal_loading.scss',
        ],
        'web.assets_backend': [
            'wm_base/static/src/scss/primary_variables.scss',
            'wm_base/static/src/scss/style.scss',
            'wm_base/static/src/js/navbar.js',
            'wm_base/static/src/js/chatter_shadow_patch.js',
            'wm_base/static/src/xml/navbar.xml',
            'wm_base/static/src/css/wm_dashboard.css',
            'wm_base/static/src/components/wm_dashboard.xml',
            'wm_base/static/src/components/wm_dashboard.js',
            'wm_base/static/src/js/sign_now_dashboard.js',
            'wm_base/static/src/xml/sign_now_dashboard.xml',
            'wm_base/static/src/css/sign_now_dashboard.css',
        ],
        'web.assets_backend_lazy': [
            'wm_base/static/src/js/graph_renderer_patch.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
