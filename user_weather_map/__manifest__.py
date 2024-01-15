# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
{
    'name': 'User Weather Notification',
    'version': '17.0.1.0.0',
    'category': 'Productivity',
    'summary': """The User Weather Notification Odoo app is an extension module 
     that integrates weather forecasting functionality into the Odoo ERP 
     system""",
    'description': """The User Weather Notification app enhances the usability 
     of the Odoo platform by integrating weather data and alerts. It enables 
     users to stay informed about weather conditions and receive timely 
     notifications based on their chosen locations'""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['web'],
    'data': ['views/res_users_views.xml'],
    'assets': {
        'web.assets_backend': [
            'user_weather_map/static/src/js/WeatherMenu.js',
            'user_weather_map/static/src/xml/weather_notification_templates.xml',
        ],
    },
    'external_dependencies': {
        'python': ['geocoder'],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
