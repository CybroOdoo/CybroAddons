# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2018-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU AGPL (v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AGPL (AGPL v3) for more details.
#
##############################################################################
{
    'name': 'Mobile Service Management',
    'version': '12.0.1.0.0',
    'summary': 'Module for managing mobile service shop daily activities.',
    'category': 'Industries',
    'author': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['stock_account', 'mail', 'product', 'account'],
    'data': ['security/security.xml',
             'security/ir.model.access.csv',
             'views/mobile_service_views.xml',
             'wizard/mobile_create_invoice_views.xml',
             'reports/mobile_service_ticket.xml',
             'reports/service_ticket_template.xml',
             'data/mobile_service_data.xml',
             'data/mobile_service_email_template.xml'],
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'AGPL-3',
}