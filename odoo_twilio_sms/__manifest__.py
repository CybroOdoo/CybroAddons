# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
{
    'name': 'Twilio SMS Gateway',
    'version': '20.0.1.0.0',
    'category': 'Productivity',
    'summary': 'Send individual and group SMS through the Twilio gateway.',
    'description': 'Send SMS through Twilio from sale orders, purchase '
                   'orders and contacts. Create reusable message templates '
                   'and send SMS to groups of contacts, immediately or on a '
                   'scheduled date.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale', 'purchase', 'sms'],
    'data': [
        'security/ir.access.csv',
        'data/ir_cron_data.xml',
        'views/purchase_order_views.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/twilio_account_views.xml',
        'views/twilio_sms_group_views.xml',
        'views/twilio_sms_template_views.xml',
        'views/twilio_sms_views.xml',
        'wizard/sms_builder_views.xml',
    ],
    'external_dependencies': {
        'python': ['twilio'],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
