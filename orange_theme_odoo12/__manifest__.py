# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    "name": "Outrageous Orange Backend Theme",
    "description": """Backend theme for Odoo 14.0 community edition.""",
    "summary": "Outrageous Orange Backend Theme",
    'version': '14.0.1.0.0',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    "website": "https://www.cybrosys.com",
    "category": "Themes/Backend",
    'images': [
        'static/description/banner.png',
        'static/description/theme_screenshot.png',
    ],
    "depends": [
        'website',
        'portal',
        'web_responsive'
    ],
    "data": [
        'views/assets.xml',
        'views/login_templates.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
