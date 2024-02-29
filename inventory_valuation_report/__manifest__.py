# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sumith Sivan(<https://www.cybrosys.com>)
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
    'name': 'Inventory Valuation Report',
    'version': '16.0.1.0.0',
    'summary': """This Module will print the report for your inventory 
    valuation""",
    'description': """This Module helps to get a systematic analysis of 
    the inventory valuation""",
    'category': 'Inventory',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'depends': ['base', 'stock', 'purchase', 'web', 'sale_management'],
    'website': 'https://www.cybrosys.com',
    'data': [
        'security/ir.model.access.csv',
        'wizards/valuation_report_views.xml',
        'report/valuation_report_pdf_templates.xml',
        'report/inventory_valuation_reports.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'inventory_valuation_report/static/src/js/action_manager.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
