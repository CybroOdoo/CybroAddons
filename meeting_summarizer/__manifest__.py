# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
    'name': 'Meeting Summarizer',
    'version': '18.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """Transcribes Discuss meetings and 
                  saves the text with a summary.""",
    'description': """This module transcribes the Discuss meeting and
     saves the transcription in a file. It also generates a summary of the meeting content.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends':['mail', 'web'],
    'data':[
        'security/ir.model.access.csv',
        'data/send_transcription_template.xml',
        'views/res_config_settings.xml',
        'views/send_mail_transcription.xml',
    ],
    "assets": {
        'web.assets_backend': [
            "meeting_summarizer/static/src/js/call_action_list.js",
            "meeting_summarizer/static/src/js/attachment_list.js",
            "meeting_summarizer/static/src/xml/attachment_list.xml",
        ],
        'mail.assets_public': [
            "meeting_summarizer/static/src/js/call_action_list.js",
            "meeting_summarizer/static/src/js/attachment_list.js",
            "meeting_summarizer/static/src/xml/attachment_list.xml",
        ],
    },
    'external_dependencies': {
            'python': ['openai'],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
