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
    'name': 'Multiple SMS Gateway Integration',
    'version': '20.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Module to send SMS through different SMS gateways',
    'description': """This module helps to send SMS using different SMS 
                    gateways including Twilio, Vonage, TeleSign.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'contacts',
        'mail',
        'phone_validation',
    ],
    'data': [
        'security/multi_sms_gateway_groups.xml',
        'security/ir.access.csv',
        'security/sms_history_security.xml',
        'data/sms_gateway_data.xml',
        'views/sms_history_views.xml',
        'views/sms_gateway_config_views.xml',
        'views/res_partner_views.xml',
        'wizard/send_sms_views.xml',
        'views/multi_sms_gateway_menus.xml',
    ],
    'external_dependencies': {
        'python': ['telesign', 'twilio', 'vonage'],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False
}
