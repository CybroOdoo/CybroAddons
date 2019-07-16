# -*- coding: utf-8 -*-

##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nikhil krishnan(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'User Weather Notification',
    'version': '10.0.1.0',
    'summary': """Get User's Weather From OpenWeatherMap Automatically.""",
    'description': """Get User's Weather and Temperature From OpenWeatherMap Automatically.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'http://www.cybrosys.com',
    'category': 'Tools',
    'depends': ['base'],
    'external_dependencies': {'python': ['pytemperature']},
    'license': 'LGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'views/weather_template.xml',
        'views/weather_conf.xml',
    ],
    'demo': [],
    'qweb': [
        "static/src/xml/weather_topbar.xml",
    ],
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
}
