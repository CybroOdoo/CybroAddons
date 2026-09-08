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
    'name': 'Waste Management Compliance',
    'version': '19.0.1.0.0',
    'category': 'Operations/Waste Management',
    'summary': 'Regulatory and legal compliance management for waste streams.',
    'description': """
        Waste Management Compliance Module
        ===================================
        Handles regulatory and legal tracking for Hazardous, Bio-Medical, E-Waste, and C&D waste streams.
        Provides custom digital signatures, state-locking (immutability), permit vaults, and PDF/XLSX reports.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Technologies Pvt. Ltd.',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'wm_base',
        'base',
        'web',
        'mail',
        'portal',
        'wm_collection',
    ],
    'external_dependencies': {
        'python': ['openpyxl', 'pypdf'],
    },
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        'report/report_actions.xml',
        'report/report_templates.xml',
        'views/disposal_facility_views.xml',
        'views/compliance_manifest_views.xml',
        'views/compliance_certificate_views.xml',
        'views/compliance_target_views.xml',
        'views/compliance_document_views.xml',
        'views/dashboard_views.xml',
        'views/menus.xml',
    ],
    'demo': [
        'demo/demo_compliance_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'wm_compliance/static/src/css/compliance_dashboard.css',
            'wm_compliance/static/src/components/compliance_dashboard.xml',
            'wm_compliance/static/src/components/compliance_dashboard.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
