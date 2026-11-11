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
    'name': "Systray World Clock",
    'version': '20.0.1.0.0',
    'category': 'Productivity',
    'summary': "Keep track of the time in different countries around the world.",
    'description': """This module adds a world clock in the systray which
                    displays the time in different countries around the world.
                    The timezone can be customized in the settings.""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['web'],
    'data': [
        'security/ir.access.csv',
        'views/systray_world_clock_config_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'systray_world_clock/static/src/js/SystrayWorldClock.js',
            'systray_world_clock/static/src/xml/systray_world_clock.xml',
            'systray_world_clock/static/src/scss/systray_world_clock.scss',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
