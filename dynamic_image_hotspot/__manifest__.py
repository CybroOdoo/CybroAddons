# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ansil pv (odoo@cybrosys.com)
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
    'name': 'Dynamic Image Hotspot',
    'version': '16.0.1.0.0',
    'category': 'Website',
    'summary': 'Add dynamic hotspot for snippet images',
    'description': "The app allows users to add a hotspot for snippet images. "
                   "A product link can be further added to the hotspot so that "
                   "whenever a user clicks on the hotspot they are directed to "
                   "the product page in website shop.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website_sale'],
    'data': ['views/snippets/snippets.xml'],
    'assets': {
        'website.assets_wysiwyg': [
            'dynamic_image_hotspot/static/src/js/snippet_options.js',
            'dynamic_image_hotspot/static/src/css/style.css',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
