# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anfas Faisal K (odoo@cybrosys.com)
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
    'name': 'Advanced Search In Systray',
    'version': '17.0.1.0.0',
    'category': 'Extra Tools',
    'summary': "Advanced Search in Systray enables Users to search the records"
               "based on name in any Module.",
    'description': "The Advanced Search Systray is a feature-rich Odoo module "
                   "designed to elevate the search experience for users. With "
                   "a focus on simplicity and effectiveness, this tool allows "
                   "users to conduct searches seamlessly across all modules "
                   "within the Odoo platform.",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'depends': ['base'],
    'website': "https://www.cybrosys.com",
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'master_search_systray/static/src/css/style.css',
            'master_search_systray/static/src/scss/master_search_bar.scss',
            'master_search_systray/static/src/xml/master_search_icon.xml',
            'master_search_systray/static/src/js/master_search_icon.js',
            'master_search_systray/static/src/js/MasterSearchDialog.js',
            'master_search_systray/static/src/xml/MasterSearchDialog.xml'
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
