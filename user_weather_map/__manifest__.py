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
    'name': 'User Weather Notification',
    'version': '20.0.1.0.0',
    'category': 'Productivity',
    'summary': "Show the current weather for each user in the Odoo systray.",
    'description': """The User Weather Notification app shows each user the
     current weather for their chosen location in the Odoo systray.""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['web'],
    'data': ['views/res_users_views.xml'],
    'assets': {
        'web.assets_backend': [
            'user_weather_map/static/src/scss/weather_menu.scss',
            'user_weather_map/static/src/js/WeatherMenu.js',
            'user_weather_map/static/src/xml/weather_notification_templates.xml',
        ],
    },
    'external_dependencies': {
        'python': ['geocoder'],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
