# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nimisha Muralidhar (odoo@cybrosys.com)
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
    'name': 'Batch Manufacturing Orders',
    'version': '13.0.1.0.0',
    'category': 'Manufacturing/Manufacturing',
    'summary': 'Produce products for multiple manufacturing orders',
    'description': 'Produce products for multiple manufacturing orders',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'images': ['static/description/banner.png'],
    'website': 'https://www.cybrosys.com',
    'depends': ['mrp'],
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_production_views.xml',
        'wizard/wizard_views.xml',
            ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,

}

