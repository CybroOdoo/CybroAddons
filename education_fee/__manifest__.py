# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Gayathri V (odoo@cybrosys.com)
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
################################################################################
{
    "name": "Educational Fee Management",
    "version": '18.0.1.0.0',
    "category": 'Industries',
    'summary': """Education fee is the core module of Educational ERP software, 
     a management application for effective school run .""",
    'description': """Education fee provides a comprehensive student fee
     management solution to automate, streamline and transform fee processing
     in educational institutions.""",
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    'maintainer': 'Cybrosys Techno Solutions',
    "website": "http://www.educationalerp.com",
    "depends": ['account', 'education_core',],
    "data": [
        'security/ir.model.access.csv',
        'views/education_fee_structure_menu_views.xml',
        'views/account_move_views.xml',
        'views/education_fee_structure_views.xml',
        'views/education_fee_type_views.xml',
        'views/education_fee_category_views.xml',
        'views/account_journal_templates.xml',
        'views/account_journal_views.xml',
    ],
    'demo': [
        'demo/account_account_demo.xml',
        'demo/account_journal_demo.xml',
        'demo/education_fee_category_demo.xml',
        'demo/education_fee_structure_demo.xml',
        'demo/education_fee_type_demo.xml',
        'demo/education_fee_structure_lines_demo.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    "installable": True,
    "auto_install": False,
    'application': True,
}
