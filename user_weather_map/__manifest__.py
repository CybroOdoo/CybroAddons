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
    'version': '15.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """Users can see Weather Notification by using openweathermap API'""",
    'description': """ The Weather Notification feature in Odoo is designed
     to provide real-time weather updates and alerts to users within the Odoo
     system. This feature can be highly beneficial for businesses that depend
     on weather conditions, such as logistics, agriculture, construction,
     and outdoor event management.'""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base'],
    'data': [
        'views/res_users_views.xml'
    ],
    'assets': {
        'web.assets_backend': {
            'user_weather_map/static/src/scss/weather.scss',
            'user_weather_map/static/src/js/weather_notification.js',
        },
        'web.assets_qweb': {
            'user_weather_map/static/src/xml/weather_notification_templates.xml',
        },
    },
    'images': ['static/description/banner.png'],
    'external_dependencies': {
        'python': ['geocoder'],
    },
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
