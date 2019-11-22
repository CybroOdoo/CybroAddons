# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sayooj A O(<https://www.cybrosys.com>)
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
    'name': 'POS waiter performance analysis',
    'summary': """Allows waiter selection from pos interface and
    			provides report for performance analysing""",
    'version': '12.0.1.0.0',
    'description': """Allows waiter selection from pos interface and
   					 provides report for analysing the performance of the waiter""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'category': 'Point of Sale',
    'depends': ['base', 'point_of_sale', 'hr'],
    'license': 'AGPL-3',
    'data': [
        'views/pos_employee_template.xml',
        'views/hr_employee_view_inherited.xml',
        'views/pos_order_waiter_inherited.xml',
        'views/pos_config_inherited_view.xml',
        'wizard/waiter_performance_wizard_view.xml',
        'report/waiter_performance_report.xml',
        'report/waiter_performance_report_template.xml',
    ],
    'qweb': ['static/src/xml/pos_waiter_selection.xml'],
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,

}
