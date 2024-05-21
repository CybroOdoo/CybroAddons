# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': "BOM Comparison Report",
    'version': '15.0.1.0.0',
    'category': 'Manufacturing',
    'description': 'Get the Comparison report based on the cost or sales price '
               'analysis for the selected Bill of materials',
    'summary': 'Comparison Report Of Bom Based on Analysis Method',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['mrp'],
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_bom_views.xml',
        'reports/bom_comparison_template.xml',
        'reports/ir_actions_report.xml',
        'wizards/bom_comparison_views.xml',
    ],
    'assets': {
       'web.assets_backend': [
           'bom_comparison_report/static/src/js/bom_compare_button.js',
       ],
       'web.assets_qweb': [
           'bom_comparison_report/static/src/xml/bom_compare_button_template.xml',
       ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}

