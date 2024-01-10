# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Process Cost of Manufacturing Orders',
    'version': '16.0.1.0.0',
    'category': 'Manufacturing',
    'summary': """Manufacture Process Costing By Material Cost, Labour Cost and
     Overhead Cost""",
    'description': """This module helps to calculate process cost of 
     manufacturing order and workorder with material cost, labour cost and 
     overhead cost from components and work center. It calculates both 
     estimated costing and real costing. Estimated costing is done on Bill of 
     Material-BOM and real costing calculated on manufacturing order based on 
     real-time consumption and quantity consumption. You can also provide a 
     cancel reason for canceling the manufacture order.You can also see the 
     reports for BOM and Manufacture order. Also, you can add cancel 
     reasons.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://cybrosys.com',
    'depends': ['base', 'mrp'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/mrp_bom_views.xml',
        'views/mrp_production_views.xml',
        'views/mrp_workcenter_views.xml',
        'views/mrp_cancel_reason_views.xml',
        'report/mrp_bom_cost_reports.xml',
        'report/mrp_bom_cost_report_templates.xml',
        'report/mrp_production_cost_reports.xml',
        'report/mrp_production_cost_report_templates.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
