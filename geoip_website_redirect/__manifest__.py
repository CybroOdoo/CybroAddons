# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohammed Dilshad Tk (odoo@cybrosys.com)
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
###############################################################################
{
    'name': 'Website Language And Currency Based On GeoIP',
    'version': '15.0.1.0.0',
    'category': 'eCommerce, Productivity',
    'summary': """This module helps you to map currency and language
     based on Customer's IP address for Odoo 15""",
    'description': """Website Language And Currency Based On GeoIP Application
     module helps the user to view website and its contents in the language of 
     country from which the user login and also able to view the website shop's 
     currency as that country's currency""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://cybrosys.com',
    'depends': ['website_sale'],
    'data': ['views/geoip_website_redirect_templates.xml'],
    'assets': {
        'web.assets_frontend': [
            'geoip_website_redirect/static/src/js/user_ip.js', ],
    },
    'external_dependencies': {
        'python': ['countryinfo'],
    },
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,

}
