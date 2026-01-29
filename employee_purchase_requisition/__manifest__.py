# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Shonima(<https://www.cybrosys.com>)
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
#############################################################################
{
    'name': 'Employee Purchase Requisition',
    'version': '15.0.1.0.0',
    'category': 'Purchases',
    'summary': 'This app allows an employee to submit a request to the '
               'purchasing department or management for the purchase of goods '
               'or services.',
    'description': 'This app allows employees to request purchases from the '
                   'company. They make requests for goods or services through '
                   'the purchasing department or management.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['hr', 'stock', 'purchase'],
    'data': [
        'security/employee_purchase_requisition_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ir_actions_server_data.xml',
        'views/employee_purchase_requisition_views.xml',
        'views/employee_purchase_requisition_menu_items.xml',
        'views/hr_employee_views.xml',
        'views/hr_department_views.xml',
        'views/purchase_order_views.xml',
        'views/stock_picking_views.xml',
        'views/requisition_order_views.xml',
        'report/employee_purchase_requisition_templates.xml',
        'report/employee_purchase_requisition_reports.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
