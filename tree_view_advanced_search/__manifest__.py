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
    'name': 'Tree View Advanced Search',
    'version': '20.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """Advanced search in all list views""",
    'description': 'A longer description of what this module does.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['web', 'purchase', 'account', 'sale'],
    'assets': {
        'web.assets_backend': [
            'tree_view_advanced_search/static/src/js/components/date_range.js',
            'tree_view_advanced_search/static/src/js/components/date_range.xml',
            'tree_view_advanced_search/static/src/css/search_bar_view.css',
            'tree_view_advanced_search/static/src/js/list_renderer_search_bar.js',
            'tree_view_advanced_search/static/src/xml/list_renderer_search_bar.xml',
        ],
        'web.assets_unit_tests': [
            'tree_view_advanced_search/static/tests/**/*.test.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
