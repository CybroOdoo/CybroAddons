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
#############################################################################
{
    'name': 'Personal Organiser',
    'version': '20.0.1.0.0',
    'category': 'Extra Tools',
    'summary': "Manage notes, tasks and contacts from a sidebar in every view.",
    'description': """Lets each user manage their notes, tasks and contacts
     from a sidebar available in every Odoo view.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'web', 'calendar'],
    'data': ['security/ir.access.csv',
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
            'personal_organiser/static/src/webclient/notemaker/notemaker_templates.xml',
            'personal_organiser/static/src/webclient/contacts/contacts_templates.xml',
            'personal_organiser/static/src/webclient/calender/calender_templates.xml',
            'personal_organiser/static/src/webclient/sidebar/sidebar.xml',
            'personal_organiser/static/src/webclient/personalorganiser/organizer.scss',
            'personal_organiser/static/src/webclient/notemaker/notemaker.scss',
            'personal_organiser/static/src/webclient/calender/calender.scss',
            'personal_organiser/static/src/webclient/organiser_panels.scss',
        ],
    },
    'license': 'LGPL-3',
    'images': [
        'static/description/banner.jpg',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
