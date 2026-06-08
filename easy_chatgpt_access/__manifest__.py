# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################
{
    'name': 'Easy ChatGPT Access',
    'version': '19.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """Access ChatGPT from systray.""",
    'description': """This module enables easy access to the ChatGPT dialog box
    from the systray icon and allows copying the generated text to the
    clipboard.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['html_editor'],
    'assets': {
        'web.assets_backend': [
            'easy_chatgpt_access/static/src/css/chatgpt_chat.css',
            'easy_chatgpt_access/static/src/xml/chatgpt_button_views.xml',
            'easy_chatgpt_access/static/src/xml/chatgpt_prompt_dialog.xml',
            'easy_chatgpt_access/static/src/xml/EasyChatGPTDialog.xml',
            'easy_chatgpt_access/static/src/js/chatgpt_button.js',
            'easy_chatgpt_access/static/src/js/wysiwyg.js',
            'easy_chatgpt_access/static/src/js/ChatGPTPromptDialog.js',
            'easy_chatgpt_access/static/src/js/chatgpt_dialog.js',
            'easy_chatgpt_access/static/src/js/EasyChatGPTDialog.js',
        ],
    },

    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}

