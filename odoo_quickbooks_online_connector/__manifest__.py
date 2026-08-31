# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
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
    'name': "Odoo Quickbooks Online Connector",
    'version': '19.0.1.0.0',
    'category': 'Productivity',
    'summary': """This module helps to import/export data between Odoo and  Quickbooks""",
    'description': """Odoo Quickbooks Online Connector allows you to integrate 
 your Odoo with Quickbooks Online Application. The module allows you to 
 easily import and export the data""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['contacts', 'sale_management', 'stock', 'hr',
                'purchase', 'account', 'queue_job'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_category_views.xml',
        'views/product_product_views.xml',
        'views/account_account_views.xml',
        'views/res_partner_views.xml',
        'views/hr_employee_views.xml',
        'views/tax_agency_views.xml',
        'views/account_tax_views.xml',
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
        'views/purchase_order_views.xml',
        'views/account_payment_views.xml',
        'wizard/asset_account_product_views.xml',
        'views/quickbooks_connector_views.xml',
        'views/qbooks_logs_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'OPL-1',
    'price': 99,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
    'application': True,
}
