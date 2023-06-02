# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohamed Muzammil VP(odoo@cybrosys.com)
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
################################################################################
{
    'name': 'User Weather Notification',
    'version': '15.0.1.0.0',
    'summary': """Weather Notification in odoo'""",
    'description': """Users can see Weather Notification by using 
                      openweathermap API'""",
    'category': 'Extra Tools',
    'depends': ['web', 'base', 'sale'],
    'author': "Cybrosys Techno Solutions",
    'website': "https://www.cybrosys.com",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'data': ['views/res_users_views.xml'],
    'images': ['static/description/banner.jpg'],
    'assets': {
        'web.assets_backend': {
            'user_weather_notification/static/src/scss/weather.scss',
            'user_weather_notification/static/src/js/weather_notification.js',
        },
        'web.assets_qweb': {
            'user_weather_notification/static/src/xml/weather_notification_templates.xml',
        },

    },
    'external_dependencies': {
        'python': ['geocoder'],
    },
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
