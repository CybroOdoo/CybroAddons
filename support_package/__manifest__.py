# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Support Package Management',
    'summary': 'Support Service and Package Management Module',
    'description': """Support Module is an easy-to-use Support Management app.
                     It enables users to create, manage, optimize, and monitor 
                     the entire service request from a centralized application.
                     """,
    'author': "Cybrosys Techno Solutions",
    'website': "https://www.cybrosys.com",
    'company': "Cybrosys Techno Solutions",
    'maintainer': "Cybrosys Techno Solutions",
    'category': 'Project',
    'Version': '14.0.1.0.0',
    'depends': ['base', 'project', 'sale_management', 'hr_timesheet'],
    'data': [
        'security/ir.model.access.csv',
        'views/support_package.xml',
        'views/support_client.xml',
        'views/package_template.xml',
        'report/support_report_views.xml',
    ],
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
