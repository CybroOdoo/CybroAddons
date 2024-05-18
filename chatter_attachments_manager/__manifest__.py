# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sabeel B (odoo@cybrosys.com)
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
################################################################################
{
    'name': 'Chatter Attachment Manager',
    'version': '17.0.1.0.0',
    'category': 'Discuss, Document Management',
    'summary': 'This module help to manage attachments',
    'description': """This module helps to enhance the attachment management 
    capabilities within Odoo.Can easily edit,read, save, preview your documents 
    inside odoo. Module works in discuss, chat and chatter of any record""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'mail', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/ir_attachment_views.xml',
        'views/ir_attachment_tag_views.xml',
        'report/chatter_attachments_manager_report_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'https://cdnjs.cloudflare.com/ajax/libs/fabric.js/3.6.0/fabric.js',
            'https://uicdn.toast.com/tui.code-snippet/v1.5.0/tui-code-snippet.min.js',
            'https://uicdn.toast.com/tui-color-picker/v2.2.6/tui-color-picker.js',
            'https://cdnjs.cloudflare.com/ajax/libs/FileSaver.js/1.3.3/FileSaver.min.js',
            'https://uicdn.toast.com/tui-image-editor/latest/tui-image-editor.js',
            'https://uicdn.toast.com/tui-image-editor/latest/tui-image-editor.css',
            'chatter_attachments_manager/static/src/attachment_control_panel/'
            'attachment_control_panel_templates.xml',
            'chatter_attachments_manager/static/src/attachment_control_panel/'
            'attachment_control_panel.js',
            'chatter_attachments_manager/static/src/attachment_image/'
            'attachment_image.js',
            'chatter_attachments_manager/static/src/registry/registry.js',
            'chatter_attachments_manager/static/src/css/'
            'chatter_attachment_manager.css',
            'chatter_attachments_manager/static/src/attachment_image/'
            'attachment_image_templates.xml',
        ],
    },
    'external_dependancy': ['pandas', 'qrcode', 'python-docx'],
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False
}
