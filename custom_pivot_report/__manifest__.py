# -*- coding: utf-8 -*-
#############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Sreerag PM(odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU LESSER
# GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
# You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
# (LGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Custom Pivot Report',
    'version': '14.0.1.0.0',
    "category": "Extra Tools",
    "summary": """Create Custom Pivot Report For Any Model Without Coding""",
    "description": """Create Custom Pivot Report For Any Model Without Coding, 
     Dynamic Pivot Report, Custom Pivot Report, Dynamic Report, Pivot View""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/custom_report.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
    'uninstall_hook': 'report_uninstall_hook'
}
