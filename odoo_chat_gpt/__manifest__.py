# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': "ChatGPT In Odoo",
    'version': '16.0.1.0.0',
    'category': 'Productivity',
    'summary': 'Manage ChatGPT in Systray',
    'description': """This module helps to access ChatGPT in Systray and Get 
     chat history""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'website'],
    'data': [
             'views/res_config_settings_views.xml'
    ],
    'assets': {
       'web.assets_backend': [
           '/odoo_chat_gpt/static/src/js/chat_gpt.js',
           '/odoo_chat_gpt/static/src/xml/chat_gpt_templates.xml',
           '/odoo_chat_gpt/static/src/css/chat_gpt.css'
       ],
   },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
