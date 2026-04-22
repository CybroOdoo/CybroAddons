# -*- coding: utf-8 -*-
#############################################################################
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
    'name': 'Oil & Gas Inspection',
    'version': '19.0.1.0.0',
    'category': 'Oil ERP/Downstream',
    'summary': 'Manufacturing Inspection for Oil & Gas Downstream',
    'description': """
Inspection module for Oil & Gas downstream manufacturing.

Flow:
─────
1. Enable "Inspection & Checklist" in Oil ERP → Configuration → Settings
2. Create Inspection Points (templates) under Configuration
3. When a Manufacturing Order is marked Done, an "Inspect" button appears
4. Click Inspect → opens an Inspection Order pre-filled from the Inspection Point
5. Inspector fills Pass/Fail + Remarks on each checklist line
6. Mark the Inspection as Passed or Failed
7. Smart button on the MO shows inspection count and overall status
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'oil_erp_base',
        'oil_erp_manufacturing',
        'mrp',
        'mail',
    ],
    'data': [
        'security/oil_inspection_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/oil_inspection_point_views.xml',
        'views/oil_inspection_order_views.xml',
        'views/mrp_production_views.xml',
        'views/oil_inspection_menus.xml',
        'views/inspection_reporting_views.xml',
        'wizard/inspection_fail_wizard_views.xml',
    ],
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
