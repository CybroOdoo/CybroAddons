# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

{
    'name': 'Information Management System',
    'version': '19.0.1.0.0',
    'category': 'Productivity/Information',
    'summary': 'Build, organise, and expand your centralised info hub',
    'description': (
        'Bring all your info together in one place to manage, share, '
        'and grow it effortlessly. Supports workspaces (public / shared / '
        'private), hierarchical articles, per-article member permissions, '
        'and a modern OWL-powered two-column reading/editing experience.'
    ),
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'mail', 'web', 'website', 'html_editor', 'portal', 'web_hierarchy'],

    'data': [
        'security/info_hub_security.xml',
        'security/ir.model.access.csv',
        'views/info_hub_template_category_views.xml',
        'wizard/info_hub_assign_reading_wizard_views.xml',
        'wizard/info_hub_add_to_template_wizard_views.xml',
        'views/info_hub_article_views.xml',
        'views/info_hub_public_templates.xml',
        'views/info_hub_portal_templates.xml',
        'data/info_hub_template_data.xml',
        'views/info_hub_article_member_views.xml',
        'views/info_hub_article_stage_views.xml',
        'views/info_hub_article_reading_views.xml',
        'views/info_hub_menus.xml',
    ],

    'assets': {
        'web.assets_web_dark': [
            'info_hub/static/src/css/info_hub_app.dark.scss',
        ],
        'web.assets_backend': [
            'info_hub/static/src/css/info_hub_app.css',
            'info_hub/static/src/xml/info_hub_app.xml',
            'info_hub/static/src/xml/info_hub_sidebar.xml',
            'info_hub/static/src/xml/info_hub_templates_dialog.xml',
            'info_hub/static/src/xml/embedded_kanban.xml',
            'info_hub/static/src/xml/embedded_card_view.xml',
            'info_hub/static/src/xml/info_hub_hidden_articles_dialog.xml',
            'info_hub/static/src/js/info_hub_sidebar.js',
            'info_hub/static/src/js/embedded_kanban.js',
            'info_hub/static/src/js/embedded_card_view.js',
            'info_hub/static/src/xml/info_hub_share_panel.xml',
            'info_hub/static/src/xml/info_hub_invite_dialog.xml',
            'info_hub/static/src/xml/info_hub_cover_dialog.xml',
            # OWL component logic
            'info_hub/static/src/xml/article_search_dialog.xml',
            'info_hub/static/src/js/info_hub_app.js',
            'info_hub/static/src/js/info_hub_templates_dialog.js',
            'info_hub/static/src/js/info_hub_share_panel.js',
            'info_hub/static/src/js/info_hub_invite_dialog.js',
            'info_hub/static/src/js/info_hub_cover_dialog.js',
            'info_hub/static/src/js/info_hub_hidden_articles_dialog.js',
            'info_hub/static/src/js/foldable_section_plugin.js',
            'info_hub/static/src/js/clipboard_plugin.js',
            'info_hub/static/src/js/article_search_dialog.js',
            'info_hub/static/src/js/article_plugin.js',
            'info_hub/static/src/js/info_hub_article_form.js',
        ],
        'web.assets_frontend': [
            ('include', 'html_editor.assets_editor'),
            'info_hub/static/src/css/info_hub_app.css',
            'info_hub/static/src/js/foldable_section_plugin.js',
            'info_hub/static/src/js/clipboard_plugin.js',
            'info_hub/static/src/js/info_hub_portal.js',
            'info_hub/static/src/js/info_hub_portal_editor.js',
        ],
    },

    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
