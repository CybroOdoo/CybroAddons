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
    'name': 'NHS Trust Management — Reports & Documents',
    'version': '19.0.1.0.0',
    'category': 'Healthcare/NHS',
    'summary': 'NHS Bckoffice Operations in Odoo, Trust Management - Reports & Documents, Trust Profile PDF reports, Excel directory exports',
    'description': """NHS Trust Management - Foundation provides the core framework for managing NHS Trust governance, 
    leadership, workflows, security access, and NHS England and Scotland organizational master data within Odoo, NHS, NHS Odoo, NHS Trust Management,
    ICB Management, NHS Backoffice, NHS Operations, NHS Governance, Trust Profile PDF reports, Excel directory exports""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['odoo_nhs_trust_operations'],
    'external_dependencies': {'python': ['xlsxwriter']},
    'data': [
        'security/ir.model.access.csv',
        'wizards/nhs_trust_directory_export_views.xml',
        'views/nhs_trust_menus_inherit.xml',
        'reports/nhs_trust_profile_report.xml',
        'reports/nhs_trust_profile_template.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'application': False,
    'installable': True,
    'auto_install': False,
}
