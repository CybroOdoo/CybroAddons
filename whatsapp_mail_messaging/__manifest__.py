# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Odoo Whatsapp Connector',
    'version': '16.0.0.1.0',
    'category': 'Extra Tools',
    'summary': """Odoo Whatsapp Connector For Sales, Invoice, and Floating button in Website""",
    'description': """Added options for sending Whatsapp messages and Mails in systray bar,sale order, invoices, 
    website portal view and share the access url of documents using share option available in each records through 
    Whatsapp web..""",
    'author': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'depends': ['sale', 'account', 'website','sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/selection_messages_views.xml',
        'views/portal_whatsapp_view.xml',
        'views/sale_order_inherited.xml',
        'views/account_move_inherited.xml',
        'views/website_inherited.xml',
        'wizard/wh_message_wizard.xml',
        'wizard/portal_share_inherited.xml',
    ],
    'assets': {
        'web.assets_backend': [
            "whatsapp_mail_messaging/static/src/js/whatsapp_button.js",
            "whatsapp_mail_messaging/static/src/js/mail_button.js",
            'whatsapp_mail_messaging/static/src/xml/whatsapp_button.xml',
            'whatsapp_mail_messaging/static/src/xml/mail_button.xml',
        ],
        'web.assets_frontend': [
            "whatsapp_mail_messaging/static/src/js/whatsapp_modal.js",
            "whatsapp_mail_messaging/static/src/js/whatsapp_icon_website.js",
            "whatsapp_mail_messaging/static/src/css/whatsapp.css"
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
