# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (
#    OPL-1) It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
{
    'name': 'Inventory Report In PDF and Excel',
    "version": "18.0.1.0.0",
    'category': 'Warehouse',
    'summary': 'This module helps to Create and Print inventory reports in '
               'Excel (XLSX) and PDF format.',
    'description': 'This module helps to Create and Print inventory reports in '
                   'Excel (XLSX) and PDF format,Excel Report,Xlsx.PDF Report,'
                   'Report,Inventory.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['stock', 'stock_account', 'product_expiry'],
    'data': [
        'security/ir.model.access.csv',
        'report/ir_action_reports.xml',
        'report/stock_valuation_report_templates.xml',
        'report/stock_transfer_report_templates.xml',
        'report/stock_expiry_report_templates.xml',
        'views/stock_valuation_report_views.xml',
        'views/stock_transfer_report_views.xml',
        'views/stock_expiry_report_views.xml',
        'views/out_of_stock_report_views.xml',
        'views/report_stock_inventory_menus.xml',
        'views/stock_quantity_history_views.xml',
        'report/stock_quantity_history_templates.xml',
        'report/stock_quantity_history_reports.xml',
        'report/out_of_stock_report_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'report_stock_inventory/static/src/js/action_manager.js'
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': False,
    'price': 20,
    'currency': 'EUR',
}
