# -*- coding: utf-8 -*-
###############################################################################
#
#  Cybrosys Technologies Pvt. Ltd.
#
#  Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#  Author: Anusha C (odoo@cybrosys.com)
#
#  You can modify it under the terms of the GNU LESSER
#  GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#  You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#  (LGPL v3) along with this program.
#  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    "name": "Inventory Advanced Reports",
    "version": "16.0.1.0.1",
    "category": 'Warehouse',
    "summary": "Inventory reports to help you to manage your inventory "
               "properly",
    "description": "This module allows you to generate inventory reports,users "
                   "can track Aging analysis, FSN classification (inventory "
                   "movement frequency classification), XYZ classification "
                   "(inventory classification based on stock value), FSN-XYZ "
                   "combined classification to define sales strategies for the "
                   "existing inventories. Overstock analysis, Out of Stock "
                   "analysis and Stock movements (inventory rotation).",
    "author": "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    "depends": ["stock", "purchase", "sale_management"],
    "data": ["security/ir.model.access.csv",
             "report/aging_report_views.xml",
             "report/fsn_report_views.xml",
             "report/xyz_report_views.xml",
             "report/fsn_xyz_report_views.xml",
             "report/out_of_stock_report_views.xml",
             "report/over_stock_report_views.xml",
             "report/age_breakdown_report_views.xml",
             "report/stock_movement_report_views.xml",
             "wizard/inventory_aging_report_views.xml",
             "wizard/inventory_aging_data_report_views.xml",
             "wizard/inventory_fsn_report_views.xml",
             "wizard/inventory_fsn_data_report_views.xml",
             "wizard/inventory_xyz_report_views.xml",
             "wizard/inventory_xyz_data_report_views.xml",
             "wizard/inventory_fsn_xyz_report_views.xml",
             "wizard/inventory_fsn_xyz_data_report_views.xml",
             "wizard/inventory_out_of_stock_report_views.xml",
             "wizard/inventory_out_of_stock_data_report_views.xml",
             "wizard/inventory_age_breakdown_report_views.xml",
             "wizard/inventory_over_stock_report_views.xml",
             "wizard/inventory_over_stock_data_report_views.xml",
             "wizard/inventory_stock_movement_report_views.xml",
             ],
    'assets': {
        'web.assets_backend': [
            'inventory_advanced_reports/static/src/js/action_manager.js']
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
