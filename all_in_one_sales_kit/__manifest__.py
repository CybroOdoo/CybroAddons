# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
    'name': 'All In One Sales Kit',
    'version': '17.0.1.0.0',
    'category': 'Sales',
    'summary': 'This module combines a variety of sales features.',
    'description': 'Sale Order Line Images, Barcode Scan Support for Sales, '
                   'Advanced Sale Reports (Product Profit Report, '
                   'Sales Invoice Analysis Report, Sales Category Report, '
                   'Sales Indent Report, Sales Analysis Report, '
                   'Hourly Sales Report), Product Pack, and '
                   'Salesperson Signature for Confirm Order are some of the '
                   'features included in this module.'
                   'Previous Sale Product Rate, Create Various Sale Order '
                   'Versions, Create Custom Fields for Sale Orders, '
                   'Recognise Previous Sales of Products,'
                   'A separate quotation number,'
                   'Multiple warehouses in sale order lines,'
                   'sales order and quotation line views,'
                   'approval of the sale order discount,sales restrictions '
                   'for out-of-stock items depending on forecast and '
                   'stock level,automate the sale process,'
                   'Sales one-stop report generation,Add more than one '
                   'item to the quotation,pivot view for partner sales,'
                   'sale order archive,Dashboard.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale_management', 'delivery', 'stock'],
    'data': [
        'security/all_in_one_sales_kit_groups.xml',
        'security/ir.model.access.csv',
        'data/field_widget_data.xml',
        'data/ir_sequence_data.xml',
        'wizard/product_sale_order_history_views.xml',
        'wizard/sale_order_dynamic_fields_views.xml',
        'wizard/sale_report_advance_views.xml',
        'wizard/sale_report_analysis_views.xml',
        'wizard/sale_report_category_views.xml',
        'wizard/sale_report_indent_views.xml',
        'wizard/sale_report_invoice_views.xml',
        'wizard/sale_report_weekly_views.xml',
        'wizard/select_product_pack_views.xml',
        'views/res_config_settings_views.xml',
        'views/all_in_one_sales_kit_menus.xml',
        'views/sale_order_views.xml',
        'views/sale_order_line_views.xml',
        'views/res_users_views.xml',
        'views/sale_report_views.xml',
        'views/product_template_views.xml',
        'views/ir_fields_search_views.xml',
        'views/product_product_views.xml',
        'views/dashboard_menu.xml',
        'report/invoice_analysis_templates.xml',
        'report/sale_order_document_templates.xml',
        'report/sale_order_report_templates.xml',
        'report/sale_profit_templates.xml',
        'report/sale_reports.xml',
        'report/sales_analysis_templates.xml',
        'report/sales_category_templates.xml',
        'report/sales_indent_templates.xml',
        'report/sales_weekly_templates.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'all_in_one_sales_kit/static/src/css/sale_report.css',
            'all_in_one_sales_kit/static/src/scss/dashboard.scss',
            'all_in_one_sales_kit/static/src/js/action_manager.js',
            'all_in_one_sales_kit/static/src/js/sale_report.js',
            'all_in_one_sales_kit/static/src/js/dashboard.js',
            'all_in_one_sales_kit/static/src/xml/sale_report_templates.xml',
            'all_in_one_sales_kit/static/src/xml/dashboard_templates.xml',
            'https://cdn.jsdelivr.net/npm/chart.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
