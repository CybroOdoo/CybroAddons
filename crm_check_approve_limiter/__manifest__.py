# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Naveen K (odoo@cybrosys.com)
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
    'name': 'CheckList and Approval Process in CRM',
    'category': 'Sales/CRM',
    'version': '15.0.1.0.0',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'summary': 'Manage CRM based on CheckList and Team/Stage and'
               'Approval Process to Make Sure Everything Completed In '
               'Each Stage',
    'description': """
                CheckList and Approve Process in CRM
                =====================================
                Module to manage CRM and CheckLists.
                This module will helps to manage CRM efficiently
                by managing checklists and approval system for CRM data. """,
    'depends': [
        'base',
        'crm',
    ],
    'data': [
        'security/security.xml',
        'views/crm_stage_views.xml',
        'security/ir.model.access.csv',
        'views/crm_lead_views.xml',
    ],
    'images': [
        'static/description/banner.png'
    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
