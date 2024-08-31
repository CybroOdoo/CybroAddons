# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Sticky Notes',
    'version': "16.0.1.0.0",
    'category': 'Productivity',
    'summary': """An additional note for form views.We can create a note in the 
     form views as a sticky notes.""",
    'description': """Sticky Notes is used to stick some notes in the form view 
     only.And we can edit delete the notes at the time of creation""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base','web'],
    'data': [
        'security/ir.model.access.csv',
        'views/stick_notes_views.xml',
        'views/res_users_views.xml',
        'views/res_users_views.xml',
        'wizard/sticky_notes_views.xml',
        'wizard/sticky_notes_update_views.xml',
        'wizard/sticky_notes_delete_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'form_sticky_notes/static/src/js/ActionMenus.js',
            'form_sticky_notes/static/src/js/ViewButton.js',
            'form_sticky_notes/static/src/xml/ActionMenus.xml',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'uninstall_hook': '_uninstall_hook',
    'installable': True,
    'auto_install': False,
    'application': False,
}
