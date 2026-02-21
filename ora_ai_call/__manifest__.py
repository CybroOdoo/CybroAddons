# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': "Ora-Ai Call",
    'version': '18.0.1.0.0',
    'category': 'eCommerce',
    'summary': """Ora-Ai Call module allows us to order assistant through
     call.""",
    'description': """ Ora Call Assistant module helps us to order the products
     through a phone call.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'bus', 'mail', 'ora_ai_base','sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/inbound_call_views.xml',
        'views/vapi_squad_views.xml',
        'views/ora_ai_call_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ora_ai_call/static/src/js/call_transcript_dashboard.js',
            'ora_ai_call/static/src/xml/call_trancript_templates.xml',
            'ora_ai_call/static/src/xml/vapi_calling_templates.xml',
            'ora_ai_call/static/src/js/inbound_call.js',
        ],
    },
    'external_dependencies': {
        'python': ['zeep'],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'auto_install': False,
    'installable': True,
    'application': False,
}
