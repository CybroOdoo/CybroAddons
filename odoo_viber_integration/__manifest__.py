# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': "Viber Integration",
    'version': '17.0.1.0.0',
    'summary': """Viber chatter for backend users.""",
    'description': 'This module provides a seamless chatting experience for '
                   'users through Viber chatter integration. By incorporating '
                   'Viber, users can engage in effortless communication within '
                   'the platform. It enhances user interaction by enabling '
                   'real-time messaging, ensuring swift and convenient '
                   'exchanges between individuals.',
    'category': 'Extra Tools',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'depends': ['web'],
    'website': "https://www.cybrosys.com",
    'assets': {
        'web.assets_backend': [
            'odoo_viber_integration/static/src/js/viber_integration.js',
            'odoo_viber_integration/static/src/xml/viber_integration_templates.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
