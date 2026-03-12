# -*- coding: utf-8 -*-
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'AI Anomaly Detection - Internal Auditor',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'AI-driven anomaly detection for accounting: real-time GL scanning, duplicate detection, and spending pattern analysis.',
    'description': """
        AI-Driven Internal Auditor
        ==========================
        * Real-time General Ledger scanning for suspicious transactions
        * Machine learning-based anomaly detection (Z-Score + statistical methods)
        * Duplicate vendor bill detection
        * Spending pattern deviation alerts
        * Pre month-end close audit dashboard
        * Risk scoring for journal entries
        * Automated audit trail and reporting
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['account', 'mail', 'base_setup'],
    'data': [
        # 1. Security first
        'security/anomaly_security.xml',
        'security/ir.model.access.csv',
        # 2. Base data
        # 3. Views (actions defined here must exist before menus reference them)
        'views/anomaly_alert_views.xml',
        'views/anomaly_dashboard_views.xml',
        'views/res_config_settings_views.xml',
        'views/anomaly_rule_views.xml',
        'views/account_move_views.xml',
        # 4. Wizard views (defines action_anomaly_scan_wizard)
        'wizard/anomaly_scan_wizard_views.xml',
        # 5. Report (defines action_anomaly_report)
        'report/anomaly_report_template.xml',
        'report/anomaly_report_action.xml',
        # 6. Menus last — all actions must exist before this
        'views/menu_views.xml',
        # 7. Cron last (depends on model records being created)
        'data/ir_cron_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'account_anomaly_detector/static/src/css/anomaly_dashboard.css',
            'account_anomaly_detector/static/src/xml/anomaly_dashboard.xml',
            'account_anomaly_detector/static/src/js/anomaly_dashboard_client_action.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
    'external_dependencies': {
        'python': ['numpy', 'scipy'],
    },
}
