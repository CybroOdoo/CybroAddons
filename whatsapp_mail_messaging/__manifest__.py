# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
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
    'version': '17.0.1.1.0',
    'category': 'Extra Tools',
    'summary': """Whatsapp Odoo Integration, Odoo Whatsapp Connector, Odoo Whatsapp, Whatsapp Connector, Whatsapp Integration, Odoo17, Whatsapp, Odoo Apps""",
    'description': """Added options for sending Whatsapp messages and emails in 
    the systray bar, sale order, invoices, website portal view and ability to 
    share access URLs for documents through the share option available in each
    record using WhatsApp Web.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale', 'account', 'website', 'sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/website_templates.xml',
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
        'views/website_views.xml',
        'views/selection_message_views.xml',
        'views/res_config_settings_views.xml',
        'wizard/whatsapp_send_message_views.xml',
        'wizard/portal_share_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            "whatsapp_mail_messaging/static/src/css/icons.css",
            "whatsapp_mail_messaging/static/src/js/whatsapp_icon.js",
            "whatsapp_mail_messaging/static/src/js/mail_icon.js",
            'whatsapp_mail_messaging/static/src/xml/whatsapp_icon_template.xml',
            'whatsapp_mail_messaging/static/src/xml/mail_icon_template.xml',
        ],
        'web.assets_frontend': [
            "whatsapp_mail_messaging/static/src/css/whatsapp_icon_website.css",
            "whatsapp_mail_messaging/static/src/js/whatsapp_web_icon.js",
            "whatsapp_mail_messaging/static/src/js/whatsapp_modal.js",
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
