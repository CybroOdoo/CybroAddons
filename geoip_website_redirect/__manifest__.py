# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayisha Sumayya K (odoo@cybrosys.com)
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
    'name': 'Website GeoIP Based Language and Currency',
    'version': '16.0.1.0.0',
    'summary': 'Website GeoIP Based Language and Currency Application '
               'for Odoo 16',
    'description': """The module helps you to map currency and language
                    based on Customer's IP address""",
    'category': 'eCommerce, Productivity',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://cybrosys.com',
    'images': ['static/description/banner.png'],
    'depends': ['base', 'website_sale'],
    'data': ['views/login_template.xml'],
    'assets': {
        'web.assets_frontend': [
            'geoip_website_redirect/static/src/js/action.js', ],
    },
    'license': 'LGPL-3',
    'auto_install': False,
    'installable': True,
    'application': False,
    'external_dependencies': {
        'python': ['countryinfo'],
    }
}
