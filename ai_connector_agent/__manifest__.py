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
    'name': 'AI Agent Connector',
    'version': '17.0.1.0.0',
    'category': 'AI',
    'summary': 'Connect to different AI providers and chat with selected models',
    'description': """
        This module allows users to connect with multiple AI providers 
        like OpenAI, Gemini, Claude, etc., and interact with selected models.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base','web','mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/ai_connector_menus.xml',
        'views/ai_providers_views.xml'],
    'assets': {
        'web.assets_backend': [
            'ai_connector_agent/static/lib/marked.min.js',
            'ai_connector_agent/static/lib/highlight.min.js',
            'ai_connector_agent/static/lib/highlight.min.css',
            'ai_connector_agent/static/src/**/*',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
