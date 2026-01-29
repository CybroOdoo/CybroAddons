# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K (odoo@cybrosys.com)
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
    'name': "All in One Inventory Kit",
    'version': '15.0.1.0.0',
    'category': 'Warehouse',
    'summary': """Manage Multiple Inventory Features with One Module""",
    'description': """ All in One Inventory Kit helps to get the features like
                  Current Stock Report for all Products in each Warehouse, Add
                  brands to products, Inventory Dashboard with all necessary 
                  details, Avoid manual entry of item count in Stock Picking
                  and Use barcode to add product, Invoice From Stock Picking, 
                  All In One Report Generator,  Get product quantity reviews 
                  for each stock location from the product form and Print PDF 
                  report of them, Stock Picking From Customer Invoice and Stock
                  Picking From Supplier bill, Order Line Description of Shipment
                  and Delivery, Catch Weight of Stock, Incoming and Outgoing 
                  Picking Operations Views are included with images of their 
                  related products, Form, Tree, Kanban, Pivot, Graph and 
                  Calendar views of Incoming and Outgoing Picking Operations""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale_management', 'stock', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_move_line_views.xml',
        'views/incoming_stock_move_line_views.xml',
        'views/outgoing_stock_move_line_views.xml',
        'views/product_brand_views.xml',
        'views/dashboard_menu.xml',
        'views/font_style.xml',
        'views/stock_picking_views.xml',
        'views/product_product_views.xml',
        'views/stock_return_picking_views.xml',
        'views/stock_scrap_views.xml',
        'views/stock_valuation_layer_views.xml',
        'views/product_template_views.xml',
        'views/res_config_settings_views.xml',
        'views/account_move_views.xml',
        'reports/inventory_report.xml',
        'reports/inventory_pdf_report.xml',
        'reports/stock_picking_report.xml',
        'reports/product_product_stock_report.xml',
        'reports/product_stock_report_template.xml',
        'wizard/wizard_stock_history_views.xml',
        'wizard/picking_invoice_wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'all_in_one_inventory_kit/static/src/js/action_manager.js',
            'all_in_one_inventory_kit/static/src/js/inventory_report.js',
            'all_in_one_inventory_kit/static/src/js/lib/Chart.bundle.js',
            'all_in_one_inventory_kit/static/src/js/dashboard.js',
            'all_in_one_inventory_kit/static/src/css/inventory_report.css',
            'all_in_one_inventory_kit/static/src/css/dashboard.css',
        ],
        'web.assets_qweb': [
            'all_in_one_inventory_kit/static/src/xml/**/*',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False
}
