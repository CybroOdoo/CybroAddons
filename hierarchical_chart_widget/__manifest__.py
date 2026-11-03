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
    'name': 'Hierarchical Chart Widget',
    'version': '20.0.1.0.0',
    'category': 'Productivity',
    'summary': 'Organization Chart Widget that displays parent and child '
               'relationships',
    'description': "An Organization Chart Widget that displays both parent "
                   "and child relationships within an organization's structure.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['hr'],
    'data': [
        'views/hr_department_views.xml'
    ],
    "assets": {
        "web.assets_backend": [
            'hierarchical_chart_widget/static/src/scss/org_template_style.scss',
            'hierarchical_chart_widget/static/src/js/org_chart.js',
            'hierarchical_chart_widget/static/src/xml/org_chart_templates.xml',
        ],
    },
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
