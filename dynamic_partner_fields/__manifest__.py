# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Ajmal JK (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

{
    'name': 'Partner Custom Fields',
    'version': '14.0.1.0.0',
    'summary': """Ability To Add Custom Fields in Partner From User Level""",
    'description': """Ability To Add Custom Fields in Partner From User Level,Partner Custom Fields,
                      Partner Dynamic Fields, odoo13, Dynamic Partner Fields, Dynamic Fields, Create Dynamic Fields, Community odoo Studio""",
    'category': 'Extra Tools',
    'author': 'Frontware, Cybrosys Techno Solutions',
    'company': 'Frontware, Cybrosys Techno Solutions',
    'maintainer': 'Frontware, Cybrosys Techno Solutions',
    'website': "https://github.com/Frontware/CybroAddons",
    'depends': ['contacts'],
    'data': [
        'data/widget_data.xml',
        'security/ir.model.access.csv',
        'security/partner_security_group.xml',
        'wizard/partner_fields_view.xml',
        'views/partner_form_view.xml',
        'views/ir_fields_search_view.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
