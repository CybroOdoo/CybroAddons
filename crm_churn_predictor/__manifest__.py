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
    'name': 'CRM Churn Predictor',
    'version': '19.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'AI-powered customer churn risk scoring and retention recommendations',
    'description': """
    CRM Churn Predictor
    ===================
    Predicts customer churn risk by analyzing CRM, Sales, Helpdesk, and communication
    data. Surfaces actionable retention recommendations directly in the Odoo interface.
    
    Features:
    ---------
    * Weighted churn scoring engine (0–100 scale) using RFM signals
    * Risk levels: Low / Medium / High / Critical
    * Daily automated scoring via ir.cron
    * Smart button on customer forms showing live risk score
    * Churn dashboard with list and kanban views grouped by risk
    * Rule-based AI retention action suggestions
    * Automated CRM activities and internal alerts for high-risk customers
    * Role-based access: Churn User / Churn Manager
        """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'crm',
        'sale_management',
        'account',
        'mail',
    ],
    'data': [
        'security/ir_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/ir_cron.xml',
        'views/churn_score_views.xml',
        'views/res_partner_views.xml',
        'views/menus.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
