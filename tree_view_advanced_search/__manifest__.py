# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
    'name': 'Tree view Advanced Search',
    'version': '19.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """Advanced search feature in all tree views""",
    'description': """It enhances user experience by enabling both single and 
    multiple search capabilities across all tree view displays. It facilitates 
    multiple search filters on single columns, allowing users to easily search 
    through various data types such as text, date/datetime, many2one, integer, 
    and float columns.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['web', 'purchase', 'account','sale'],
    'assets': {
        'web.assets_backend': [
            'tree_view_advanced_search/static/src/js/components/date_range.js',
            'tree_view_advanced_search/static/src/js/components/date_range.xml',
            'tree_view_advanced_search/static/src/css/search_bar_view.css',
            'tree_view_advanced_search/static/src/js/list_renderer_search_bar.js',
            'tree_view_advanced_search/static/src/xml/list_renderer_search_bar.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
