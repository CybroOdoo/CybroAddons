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
    'name': 'Hierarchical Chart Widget',
    'version': '16.0.1.0.0',
    'category': 'Productivity',
    'summary': 'Organization Chart Widget that displays parent and child'
               ' relationships',
    'description': 'The user is looking for an Organization Chart Widget'
                   'that displays both parent and child relationships within'
                   ' an organizations structure.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['hr'],
    'data': [
        'views/hr_department_views.xml'
            ],
    "assets":
        {"web.assets_backend": [
            '/hierarchical_chart_widget/static/src/js/org_chart.js',
            '/hierarchical_chart_widget/static/src/xml/org_chart_template.xml'
            ],
            "web.assets_frontend": [
            '/hierarchical_chart_widget/static/src/scss/org_template_style.scss',
            ]},
    'images': [
        'static/description/banner.png',
        'static/description/icon.png'
    ],
    'license': 'LGPL-3',
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
