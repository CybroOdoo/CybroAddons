# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Document Management',
    'version': '19.0.1.0.0',
    'category': 'Document Management',
    'summary': """Document Management module to access document tools""",
    'description': """The Document Management module provides a quick access to create, share 
     and delete documents efficiently.This module requires BeautifulSoup and linkpreview python libraries.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website', 'hr', 'mail'],
    'data': [
        'security/enhanced_document_management_groups.xml',
        'security/enhanced_document_management_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/document_data.xml',
        'data/ir_cron_data.xml',
        'wizard/document_request_accept_views.xml',
        'wizard/document_request_reject_views.xml',
        'wizard/document_url_views.xml',
        'wizard/document_share_views.xml',
        'wizard/work_space_views.xml',
        'wizard/document_delete_trash_views.xml',
        'wizard/document_lock_views.xml',
        'views/document_tag_views.xml',
        'views/document_workspace_views.xml',
        'views/document_file_views.xml',
        'views/document_trash_views.xml',
        'views/document_request_template_views.xml',
        'views/document_template_request_views.xml',
        'views/request_document_views.xml',
        'views/document_portal_templates.xml',
        'views/res_config_settings_views.xml',
        'views/enhanced_document_management_menus.xml',
        'reports/document_template_request_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'enhanced_document_management/static/src/css/kanban.css',
            'enhanced_document_management/static/src/css/style.css',
            'enhanced_document_management/static/src/xml/Kanban_controller.xml',
            'enhanced_document_management/static/src/xml/document_preview_template.xml',
            'enhanced_document_management/static/src/views/kanban/kanban_record.js',
            'enhanced_document_management/static/src/views/kanban/kanban_renderer.js',
            'enhanced_document_management/static/src/views/kanban/kanban_controller.js',
            'enhanced_document_management/static/src/js/client_actions.js',
            'enhanced_document_management/static/src/js/document_preview_action.js',
            'https://cdnjs.cloudflare.com/ajax/libs/jquery/2.1.3/jquery.min.js',
            'https://ajax.googleapis.com/ajax/libs/jqueryui/1.11.2/jquery-ui.min.js',
            'https://cdn.jsdelivr.net/npm/@fancyapps/fancybox@3.5.6/dist/jquery.fancybox.min.css',
            'https://cdn.jsdelivr.net/npm/@fancyapps/fancybox@3.5.6/dist/jquery.fancybox.min.js'
        ],
        'web.assets_frontend': [
            'enhanced_document_management/static/src/js/portal.js',
        ]
    },
    'external_dependencies': {
        'python': ['bs4', 'linkpreview']
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
