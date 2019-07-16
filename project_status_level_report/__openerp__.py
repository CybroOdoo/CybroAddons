# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2009-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nilmar Shereef(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': "Project Status Report",
    'summary': """
        Detailed Project Analysis with XLS Diagrams""",
    'description': """
        Graphical information of Project from various aspects. Project Task list, Comparison of planned and
        actual budget and time duration for the project.
    """,
    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'website': "http://www.cybrosys.com",
    'category': 'Project',
    'version': '0.1',
    'depends': ['base', 'project', 'report_xlsx', 'project_timesheet', 'analytic'],
    'data': [
        'views/status_wizard_view.xml',
        'views/report.xml'
    ],
    'license': 'AGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
}
