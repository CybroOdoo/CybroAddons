# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': "One2many Search Widget Odoo15",
    "version": "15.0.1.0.1",
    'description': "Quick Search Feature For One2many Fields In Odoo",
    'summary': 'Quick Search Feature For One2many Fields In Odoo',
    "website": "https://www.cybrosys.com",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'category': 'Tools',
    "author": "Cybrosys Techno Solutions",
    "license": "LGPL-3",
    'depends': ['web'],
    'assets': {
        'web.assets_backend': [
            '/one2many_search/static/src/css/header.css',
            '/one2many_search/static/src/js/one2manySearch.js'
        ],
        'web.assets_qweb': [
            'one2many_search/static/src/xml/one2manysearch.xml',
        ],
    },
    "installable": True,
    "application": False,
    'images': ['static/description/banner.png'],
    'auto_install': False,
}
