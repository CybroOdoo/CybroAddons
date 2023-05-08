# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
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
    'license': 'OPL-1',
    # 'price': 4.99,  # ToDo: Please update the price before publish
    # 'currency': 'EUR',
    'installable': True,
    'auto_install': False,
    'application': False
}
