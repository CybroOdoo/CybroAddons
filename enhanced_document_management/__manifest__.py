# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Paid App Development Team (odoo@cybrosys.com)
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
    'name': 'Document Management',
    'version': '16.0.1.0.0',
    'category': 'Document Management',
    'summary': 'The Document Management module to access document tools',
    'description': 'The Document Management module provides a quick access to '
                   'create, share and delete.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://cybrosys.com',
    'depends': ['base', 'mail', 'website'],
    'data': [
        'security/enhanced_document_management_groups.xml',
        'security/enhanced_document_management_security.xml',
        'security/ir.model.access.csv',
        'data/document_data.xml',
        'data/ir_cron_data.xml',
        'views/document_workspace_views.xml',
        'views/document_file_views.xml',
        'views/res_config_settings_views.xml',
        'views/document_portal_templates.xml',
        'views/outgoing_request_document_views.xml',
        'views/incoming_request_document_views.xml',
        'views/portal_document_breadcrumb_templates.xml',
        'views/document_trash_views.xml',
        'views/document_request_templates.xml',
        'views/enhanced_document_management_menus.xml',
        'wizard/document_share_templates.xml',
        'wizard/document_share_views.xml',
        'wizard/document_url_views.xml',
        'wizard/document_tool_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'enhanced_document_management/static/src/css/kanban.css',
            'enhanced_document_management/static/src/xml/KanbanController.xml',
            'enhanced_document_management/static/src/js/search_panel_extention_model.js',
            'enhanced_document_management/static/src/js/kanbancontroller.js',
            'enhanced_document_management/static/src/js/search_document.js',
            'https://cdn.jsdelivr.net/npm/@fancyapps/fancybox@3.5.6/dist/jquery.fancybox.min.css',
            'https://cdn.jsdelivr.net/npm/@fancyapps/fancybox@3.5.6/dist/jquery.fancybox.min.js'
        ],
        'web.assets_frontend': [
            'enhanced_document_management/static/src/js/portal.js',
            'enhanced_document_management/static/src/js/portal_document_request.js',
        ]
    },
    'external_dependencies': {
        'python': ['bs4']
    },
    'images': ['static/description/banner.jpg'],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': True,
}
