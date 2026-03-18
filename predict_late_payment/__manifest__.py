# -- coding: utf-8 --
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
    'name': 'Predict Late Payments',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Late payment prediction powered by Google Gemini AI',
    'description': """
        Analyzes customer invoice and payment history to forecast the likelihood
        of delayed payments. Features include:
        - AI-powered payment risk score per customer
        - Real-time risk indicators on customer and invoice screens
        - Automated alerts and smart follow-up suggestions
        - Credit limit recommendations
        - Cash flow impact dashboard
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'mail',
        'base_setup',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/predict_late_payment_security.xml',
        'data/ir_cron_data.xml',
        'data/mail_template_data.xml',
        'views/res_config_settings_views.xml',
        'views/res_partner_views.xml',
        'views/account_move_views.xml',
        'views/payment_risk_score_views.xml',
        'views/payment_risk_dashboard_views.xml',
        'views/menus.xml',
        'wizard/send_followup_wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'predict_late_payment/static/src/css/predict_late_payment.css',
            'predict_late_payment/static/src/js/risk_badge_widget.js',
            'predict_late_payment/static/src/js/dashboard.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
