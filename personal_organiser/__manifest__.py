# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Athira K(<https://www.cybrosys.com>)
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
    'name': 'Personal Organiser',
    'version': '17.0.1.0.0',
    'category': 'Tools',
    'summary': """The module allows to manage notes,tasks,and contacts effectively.""",
    'description': """This module allows you to manage notes, tasks, and contacts effectively from all views in odoo. """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'web', 'calendar'],
    'data': ['security/ir.model.access.csv',
             ],

    'assets': {
        'web._assets_primary_variables': [
            'personal_organiser/static/src/scss/variables.scss',
        ],
        'web._assets_backend_helpers': [
            'personal_organiser/static/src/scss/mixins.scss',
        ],
        'web.assets_web_dark': [
            (
                'after',
                'personal_organiser/static/src/scss/variables.scss',
                'personal_organiser/static/src/scss/variables.dark.scss',
            ),
        ],
        'web.assets_backend': [
            (
                'after',
                'web/static/src/webclient/webclient.js',
                'personal_organiser/static/src/webclient/layout.js',
            ),
            (
                'after',
                'web/static/src/webclient/webclient.xml',
                'personal_organiser/static/src/webclient/layout.xml',
            ),
            (
                'after',
                'web/static/src/webclient/webclient.js',
                'personal_organiser/static/src/webclient/personalorganiser/personal_organiser.js',
            ),
            (
                'after',
                'web/static/src/webclient/webclient.js',
                'personal_organiser/static/src/webclient/notemaker/notemaker.js',
            ),
            (
                'after',
                'web/static/src/webclient/webclient.js',
                'personal_organiser/static/src/webclient/contacts/contacts.js',
            ),
            (
                'after',
                'web/static/src/webclient/webclient.js',
                'personal_organiser/static/src/webclient/calender/calender.js',
            ),
            (
                'after',
                'web/static/src/webclient/webclient.js',
                'personal_organiser/static/src/webclient/sidebar/sidebar.js',
            ),
            'personal_organiser/static/src/webclient/layout.scss',
            'personal_organiser/static/src/webclient/sidebar/sidebar.scss',
            'personal_organiser/static/src/webclient/personalorganiser/personal_organiser.xml',
            'personal_organiser/static/src/webclient/notemaker/notemaker.xml',
            'personal_organiser/static/src/webclient/contacts/contacts.xml',
            'personal_organiser/static/src/webclient/calender/calender.xml',
            'personal_organiser/static/src/webclient/sidebar/sidebar.xml',
            'personal_organiser/static/src/webclient/personalorganiser/organizer.scss',
            'personal_organiser/static/src/webclient/notemaker/notemaker.scss',
            'personal_organiser/static/src/webclient/contacts/contacts.scss',
            'personal_organiser/static/src/webclient/calender/calender.scss',
        ],
    },
    'license': 'AGPL-3',
    'images': [
        'static/description/banner.jpg',
        'static/description/icon.png',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
