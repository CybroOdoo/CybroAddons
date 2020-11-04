# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sayooj A O(<https://www.cybrosys.com>)
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
#############################################################################

{
    'name': "Salesperson Signature",
    'version': '14.0.1.0.0',
    'summary': """In this module allows the salesperson to add his signature and also
                    available the option for making the validate option in sales
                    visible/invisible based on the salesperson signature""",
    'description': """In this module allows the salesperson to add his signature and also
                    available the option for making the validate option in sales
                    visible/invisible based on the salesperson signature""",
    'category': 'Sales',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'sale_management'],
    'data': [
        'views/sale_signature.xml',
        'views/res_config_settings_inherited.xml',
    ],
    'license': "AGPL-3",
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
}
