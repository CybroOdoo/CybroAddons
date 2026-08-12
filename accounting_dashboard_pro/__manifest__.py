# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT
#    OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
#    THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
##############################################################################

{
    'name': 'Advanced Accounting Dashboard Pro',
    'version': '17.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Enterprise-grade, role-aware accounting dashboard with dynamic KPIs, charts, and smart alerts',
    'description': """
        Advanced Accounting Dashboard Pro
        ==================================
        A comprehensive accounting dashboard module that overcomes the limitations
        of Odoo's native journal-centric kanban dashboard.

    Key Features:
    - Role-based dashboard views (Billing Clerk, Jr. Accountant, Auditor, Accountant, CFO)
    - Real-time KPI cards (Revenue, Expenses, Net Profit, Cash Balance, AR, AP)
    - Interactive Chart.js charts (Revenue vs Expense, Cash Flow Forecast, Aging Analysis)
    - Smart lists (Overdue Invoices, Upcoming Bills, Recent Payments)
    - Budget vs Actual tracking (when budget module is installed)
    - Quick action buttons based on user role
    - Smart alerts feed for overdue items, unreconciled entries, and tax deadlines
    - Multi-company consolidated view for managers
    - User-customizable layout with period/company filters
    - Sub-200ms load with caching, lazy loading, and parallel API calls
    - Modern UI with glassmorphism, micro-animations, and dark mode support
        """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'account',
        'account_accountant',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/dashboard_security.xml',
        'views/dashboard_action.xml',
        'views/dashboard_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'accounting_dashboard_pro/static/src/**/*.js',
            'accounting_dashboard_pro/static/src/**/*.xml',
            'accounting_dashboard_pro/static/src/**/*.scss',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'OPL-1',
    'installable': True,
    'application': True,
    'auto_install': False,
}
