# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies(odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
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
    'name': 'Chatter Attachment Manager',
    'version': '16.0.1.0.0',
    'category': 'Discuss, Document Management',
    'summary': 'This module help to manage attachments',
    'description': """This module helps to enhance the attachment management 
    capabilities within Odoo.Can easily edit,read, save, preview your documents 
    inside odoo. Module works in discuss, chat and chatter of any record""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['mail', 'base', 'web', 'documents'],
    'data': [
        'security/ir.model.access.csv',
        'views/ir_attachment_views.xml',
        'views/ir_attachment_tag_views.xml',
        'report/chatter_attachments_manager_report_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'chatter_attachments_manager/static/src/attachment_control_panel/'
            'chatter_camera.js',
            'chatter_attachments_manager/static/src/attachment_control_panel/'
            'attachment_control_panel.js',
            'chatter_attachments_manager/static/src/attachment_card/'
            'attachment_card.js',
            'chatter_attachments_manager/static/src/attachment_image/'
            'attachment_image.js',
            'chatter_attachments_manager/static/src/css/'
            'chatter_attachment_manager.css',
            'chatter_attachments_manager/static/src/chatter_topbar/'
            'chatter_topbar_templates.xml',
            'chatter_attachments_manager/static/src/attachment_control_panel/'
            'attachment_control_panel_templates.xml',
            "chatter_attachments_manager/static/src/attachment_card/"
            "attachment_card_templates.xml",
            'chatter_attachments_manager/static/src/attachment_image/'
            'attachment_image_templates.xml',
        ],
    },
    'external_dependancy': ['pandas', 'qrcode', 'docx'],
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': False
}
