# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Inventory Turnover Analysis Report',
    'version': '15.0.1.0.0',
    'summary': """A module to generate inventory turnover analysis report.""",
    'description': """This will helps you to generate inventory turnover 
    analysis report in pdf, xlsx, tree view and graph view.""",
    'category': "Warehouse",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'stock', 'sale', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/fetch_data_views.xml',
        'views/turnover_graph_analysis_views.xml',
        'views/stock_quant_views.xml',
        'report/turnover_report_templates.xml',
        'wizard/turnover_report_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'inventory_turnover_report_analysis/static/src/js/action_manager.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
