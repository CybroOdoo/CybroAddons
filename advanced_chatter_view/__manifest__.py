# -*- coding: utf-8 -*-
##############################################################################
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
##############################################################################
{
    'name': 'Advanced Chatter View',
    'version': '20.0.1.0.0',
    'category': 'Discuss',
    'summary': (
        'Advanced Collapsible and Quick-Action Chatter Interface for Odoo'
    ),
    'description': (
        'Advanced Chatter View enhances the standard Odoo chatter interface '
        'by providing quick-action icons and collapsible panels for '
        'messages, log notes, and scheduled activities.'
    ),
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'mail'],
    'assets': {
        'web.assets_backend': [
            (
                'advanced_chatter_view/static/src/lib/'
                'bootstrap-icons/bootstrap-icons.css'
            ),
            'advanced_chatter_view/static/src/css/chatter_topbar.css',
            'advanced_chatter_view/static/src/js/chatter_container.js',
            'advanced_chatter_view/static/src/xml/chatter.xml',
        ],
        'web.assets_tests': [
            'advanced_chatter_view/static/tests/tours/**/*',
        ],
        'web.assets_unit_tests': [
            'advanced_chatter_view/static/tests/chatter/**/*',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
