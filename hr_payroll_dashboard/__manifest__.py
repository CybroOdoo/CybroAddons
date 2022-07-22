# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:Cybrosys Techno Solutions(odoo@cybrosys.com)
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
    'name': "HR Payroll Dashboard",
    'version': '14.0.1.0.0',
    'summary': """HR Payroll Dashboard""",
    'description': """HR Payroll Dashboard""",
    'category': 'Human Resource',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['hr_payroll_community', 'hr_attendance', 'hr_expense'],
    'data': [
        'views/assets.xml',
        'views/dashboard_view.xml',
    ],
    'license': "AGPL-3",
    'installable': True,
    'application': True,
    'images': ['static/description/banner.png'],
    'qweb': [
        "static/src/xml/payroll_dashboard.xml",
    ],
}
