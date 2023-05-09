# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
    'name': 'Multiple SMS Gateway Integration',
    'version': '16.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Module to send SMS through different SMS gateway',
    'description': """
    This modules helps to send SMS using different SMS gateways including 
    D7, Twilio, Vonage, TeleSign, MessageBird and Telnyx""",
    'author': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'external_dependencies': {
        'python': ['messagebird', 'telesign', 'telnyx', 'twilio', 'vonage']},
    'depends': ['base', 'contacts'],
    'images': ['static/description/banner.png'],
    'data': [
        'security/multi_sms_gateway_groups.xml',
        'security/sms_history_security.xml',
        'security/ir.model.access.csv',
        'data/sms_gateway_data.xml',
        'views/sms_history_views.xml',
        'views/sms_gateway_config_views.xml',
        'views/res_partner_views.xml',
        'wizard/send_sms_views.xml',
        'views/multi_sms_gateway_menus.xml'
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False
}
