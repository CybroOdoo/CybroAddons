# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Hafeesul Ali(<https://www.cybrosys.com>)
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
    'name': 'Email Management in Odoo',
    'version': '15.0.1.0.0',
    'category': 'Productivity',
    'summary': 'This Module will help to manage all type of mails in Odoo',
    'description': """Email Management in Odoo is a comprehensive module that 
    enhances the email handling capabilities of Odoo.This module is designed 
    to streamline and improve the management of all types of emails, providing
    a user-friendly interface and additional functionalities for increased
    productivity.""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['mail', 'calendar', 'note'],
    'data': [
        'security/ir.model.access.csv',
        'data/mail_icon_data.xml',
        'views/res_config_views.xml',
        'views/inbox_menu_views.xml',
        'views/mail_attachment_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            "/odoo_mail_management/static/src/css/main.css",
            "/odoo_mail_management/static/src/js/mail_home.js",
        ],
        'web.assets_qweb': [
            "/odoo_mail_management/static/src/xml/mail_page_view.xml",
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
