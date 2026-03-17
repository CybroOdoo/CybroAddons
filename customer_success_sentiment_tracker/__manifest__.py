# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
{
    'name': 'Customer Success Sentiment Tracker',
    'version': '19.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Customer Success Sentiment Tracker using AI',
    'description': """Track customer sentiment from helpdesk tickets and emails using AI""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['crm', 'helpdesk', 'website'],
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
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
