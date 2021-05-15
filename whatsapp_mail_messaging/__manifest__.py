# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sayooj A O(<https://www.cybrosys.com>)
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
    'name': 'Whatsapp And Mail Messaging',
    'version': '14.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """Module which allows to sent Whatsapp messages and Mails from any view of
    Odoo""",
    'description': """Whatsapp Odoo, Whatsapp Odoo Message, Whatsapp, Odoo Whatsapp, Module which allows to sent Whatsapp messages and Mails from any view of
    Odoo""",
    'author': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'depends': ['contacts', 'mail'],
    'data': [
        'views/assets.xml',
        'wizard/wh_message_wizard.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': [
        'static/src/xml/whatsapp_button.xml',
        'static/src/xml/mail_button.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
