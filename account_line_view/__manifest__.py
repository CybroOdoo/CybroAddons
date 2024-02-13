# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swathy K S (odoo@cybrosys.com)
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
##############################################################################
{
    'name': "Account Invoice Line Views",
    "version": "17.0.1.0.0",
    "category": "Accounting",
    "summary": "Account Invoice/Bill Lines Tree,"
               "Form,Kanban,Pivot,Graph,Calendar Views",
    "description": """This module enables users to count invoice/bill lines 
                    through various views including tree, form, kanban, pivot, 
                    graph, and calendar, facilitating comprehensive analysis 
                    and management.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['account'],
    'data': [
        'views/invoice_line_view.xml',
        'views/bill_line_view.xml',
        'views/credit_note_line_view.xml',
        'views/refund_line_view.xml',
        'views/account_move_line_view.xml'
    ],
    'images': [
        'static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
