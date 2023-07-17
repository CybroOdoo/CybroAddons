# -*- coding: utf-8 -*-

#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Vishnu P(<https://www.cybrosys.com>)
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
    'version': '16.0.1.1.0',
    'category': 'Purchases',
    'summary': 'Employee Purchase Requisition',
    'description': 'Employee Purchase Requisition',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'images': ['static/description/banner.png'],
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'hr', 'stock', 'purchase'],
    'data': [
        'security/security_access.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/purchase_requisition.xml',
        'views/menu.xml',
        'views/hr_employee_view.xml',
        'views/hr_department_view.xml',
        'views/purchase_order_view.xml',
        'views/stock_picking_view.xml',
        'views/action_print_requisition.xml',
        'report/purchase_requisition_template.xml',
        'report/purchase_requisition_report.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
