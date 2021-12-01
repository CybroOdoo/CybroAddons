# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name": "Chameleon Multi Color Backend Theme",
    "summary": "Configurable multi color backend theme for Odoo 14",
    "version": "14.0.1.0.0",
    "category": "Themes/Backend",
    "website": "https://www.cybrosys.com",
    "description": """
        Configurable multi color backend theme for Odoo 14
    """,
    'images': [
        'static/description/banner.png',
        'static/description/theme_screenshot.png',
    ],
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    "depends": [
        'website',
        'portal',
        'web_responsive',
        'mail'
    ],
    "data": [
        'security/ir.model.access.csv',
        'data/theme_data.xml',
        'views/assets.xml',
        'views/login_templates.xml',
    ],
    'qweb': [
        'static/src/xml/base_ext.xml',
        'static/src/xml/sidebar_menu_icon.xml',
        'static/src/xml/systray_ext.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
