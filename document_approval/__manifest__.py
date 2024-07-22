# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sreeshanth V S (<https://www.cybrosys.com>)
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
    'name': "Document Approval",
    "version": "16.0.1.0.1",
    "category": "Documents Management",
    "summary": "Manager can approve or reject documents",
    "description": "User can create and upload various document for approvals."
                   "Manager can approve or reject documents.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['mail'],
    'data': [
        'security/document_approval_security.xml',
        'security/ir.model.access.csv',
        'views/document_approval_team_views.xml',
        'views/document_approval_views.xml',
        'wizards/document_approve_views.xml',
        'wizards/document_reject_views.xml',
        'wizards/document_approval_signature_views.xml',
        'views/document_approval_menus.xml'
    ],
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
