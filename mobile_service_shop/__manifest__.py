# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Jumana Jabin MP (odoo@cybrosys.com)
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
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Mobile Service Management',
    'version': '18.0.1.0.0',
    'summary': 'Module for managing mobile service shop daily activities.',
    'description':'This module provides an all-in-one solution for mobile'
                  ' service centers, helping them efficiently manage operations'
                  ' while maintaining high levels of customer satisfaction.',
    'category': 'Industries',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['stock_account', 'mail', 'product', 'account' ,'sale'],
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
    'assetsq': {
        'web.assets_backend': [
            'mobile_service_shop/static/src/css/mobile_service.css',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
