# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu Vijayan KK (odoo@cybrosys.com)
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
    'name': 'User Weather Notification',
    'version': '16.0.1.0.0',
    'category': 'Productivity',
    'summary': """The User Weather Notification Odoo app is an extension module 
    that integrates weather forecasting functionality into the Odoo ERP system'""",
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
            'user_weather_notification/static/src/js/weather_notification.js',
            'user_weather_notification/static/src'
            '/xml/weather_notification_templates.xml',
        ],
    },
    'external_dependencies': {
        'python': ['geocoder'],
    },
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
