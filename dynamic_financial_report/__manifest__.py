# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Dynamic Financial Reports',
    'version': '14.0.1.0.1',
    'category': 'Accounting',
    'summary': """Dynamic Financial Reports with drill 
                down and filters– Community Edition""",
    'description': "This module creates dynamic Accounting General Ledger, Trial Balance, Balance Sheet "
                   "Proft and Loss, Cash Flow Statements, Partner Ledger,"
                   "Partner Ageing, Day book"
                   "Bank book and Cash book reports in Odoo 14 community edition.",
    'author': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'depends': ['base', 'base_accounting_kit'],
    'data': [
        'security/ir.model.access.csv',
        'views/general_ledger_view.xml',
        'views/gl_template.xml',
        'wizard/dynamic_ledger_view.xml',
        'views/templates.xml',
        'views/pl_template.xml',
        'wizard/partner_ledger_view.xml',
        'views/al_template.xml',
        'views/kit_menus.xml',
        'wizard/dynamic_partner_ageing.xml',
        'views/bank_book_pdf_template.xml',
        'views/cash_book_pdf_template.xml',
        'views/cashfl.xml',
        'views/financial_report_qweb_pdf_template.xml',
        'views/menu_dynamic_financial_reports.xml',
        'views/db_templates.xml',
    ],
    'qweb': [
        'static/src/xml/views.xml',
        'static/src/xml/tb_view.xml',
        'static/src/xml/bs_template_views.xml',
        'static/src/xml/profit_loss_template_views.xml',
        'static/src/xml/partner_ledger_views.xml',
        'static/src/xml/al_views.xml',
        'static/src/xml/bank_book_view.xml',
        'static/src/xml/cash_book_view.xml',
        'static/src/xml/cash_flow.xml',
        'static/src/xml/db_lines.xml',
    ],
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
