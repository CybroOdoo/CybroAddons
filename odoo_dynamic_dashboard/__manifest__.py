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
    'name': "Odoo Dynamic Dashboard",
    'version': '14.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """Create Configurable Dashboards Easily""",
    'description': """Create Configurable Dashboard Dynamically to get the information that are relevant to your business, department, or a specific process or need, Dynamic Dashboard, Dashboard, Dashboard Odoo""",
    'author': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'depends': ['base', 'web'],
    'data': [
        'views/dashboard_view.xml',
        'views/dynamic_block_view.xml',
        'views/dashboard_menu_view.xml',
        'security/ir.model.access.csv',
    ],
    'images': ['static/description/banner.png'],
    'qweb': ["static/src/xml/dynamic_dashboard_template.xml"],
    'license': "AGPL-3",
    'installable': True,
    'auto_install': False,
    'application': False,
}
