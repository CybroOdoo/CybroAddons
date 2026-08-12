# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1). It is forbidden to publish, distribute, sublicense, or sell
#    copies of the Software or modified copies of the Software.
#
#    The above copyright notice and this permission notice must be included in
#    all copies or substantial portions of the Software.
#
#############################################################################

{
    'name': 'Customer Success Sentiment Tracker',
    'version': '18.0.1.0.0',
    'category': 'Extra Tools',
    'sequence': 1,
    'summary': 'Customer Success Sentiment Tracker using AI',
    'description': """Track customer sentiment from helpdesk tickets and emails using AI""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['helpdesk', 'website'],
    'data': [
        'views/helpdesk_ticket_views.xml',
        'views/res_config_settings_views.xml',
        'views/res_partner_views.xml',
        'views/success_sentiment_menus.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'customer_success_sentiment_tracker/static/src/xml/customer_success_sentiment_dashboard.xml',
            'customer_success_sentiment_tracker/static/src/js/customer_success_sentiment_dashboard.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': True,
}
