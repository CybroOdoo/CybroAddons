# -*- coding: utf-8 -*-
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
    'name': "Sales Team Access Controls",
    'version': '20.0.1.0.0',
    'category': 'Sales',
    'summary': """Provides access control for Sales Team members and leaders""",
    'description': """This module enforces role based access control inside 
    sales teams. Sales Team Members can only view and manage the Sale 
    Quotations, Sale Orders and CRM Leads they personally own, so the 
    records of their colleagues stay private. Sales Team Leaders keep 
    access to their own records and additionally reach every record 
    belonging to the sales teams they lead, which gives them full 
    visibility for supervision and performance tracking. The module builds 
    on top of the standard salesperson group and adds its accesses on top 
    of it, so it works alongside the existing permission framework in both 
    Community and Enterprise editions.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['crm', 'sale_management'],
    'data': [
        'security/sales_team_access_controls_security.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
