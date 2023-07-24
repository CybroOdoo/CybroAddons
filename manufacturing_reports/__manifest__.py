# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Javid A (odoo@cybrosys.com)
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
###############################################################################
{
    'name': 'Manufacturing Reports',
    'version': '15.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'PDF & XLS Reports For Manufacturing Module',
    'description': """This module crafted by Cybrosys Technologies provides 
                      an option to print PDF & XLS report for MRP systems, 
                      also you can view the product image in the report. This 
                      works well for large and small business MRP systems.""",
    'author': 'Cybrosys Techno Solutions',
    'website': "http://www.cybrosys.com",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'depends': ['base', 'mrp'],
    'data': [
        'security/ir.model.access.csv',
        'reports/mrp_report_templates.xml',
        'reports/mrp_report_views.xml',
        'wizard/mrp_report_views.xml',
        'views/manufacturing_report_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'manufacturing_reports/static/src/js/action_manager.js',
        ]
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
