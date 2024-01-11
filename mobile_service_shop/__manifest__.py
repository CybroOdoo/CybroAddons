# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu KP S (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
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
    'name': 'Mobile Service Management',
    'version': '17.0.1.0.0',
    'summary': 'Module for managing mobile service shop daily activities.',
    'category': 'Industries',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['stock_account', 'mail', 'product', 'account'],
    'data': ['security/mobile_service_shop_security.xml',
             'security/ir.model.access.csv',
             'views/mobile_service_views.xml',
             'views/product_template_views.xml',
             'views/product_product_views.xml',
             'views/terms_and_condition_views.xml',
             'views/mobile_complaint_description_views.xml',
             'views/mobile_complaint_views.xml',
             'views/brand_models_views.xml',
             'views/mobile_brand_views.xml',
             'wizard/mobile_create_invoice_views.xml',
             'reports/mobile_service_email_template.xml',
             'reports/mobile_service_ticket.xml',
             'data/mobile_service_data.xml',
             'data/mobile_service_email_template.xml'],
    'images': ['static/description/banner.jpg'],
    'assets': {
        'web.assets_backend': [
            'mobile_service_shop/static/src/css/mobile_service.css',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
