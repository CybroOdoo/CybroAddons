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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'MRP Split Produce All',
    'version': '17.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Split Manufacturing Completion into Consumption and Finalization',
    'description': """
                Enhances the Manufacturing Order workflow by separating material consumption
                and production finalization into two independent stages.
            
                The default 'Produce All' process is modified to complete component
                consumption and inventory movements without immediately marking the
                Manufacturing Order as done. A new 'Consume Componenets' button is 
                added to Consume the componenets only with including all its related 
                validations and warnings and a 'Finalize Production' action is
                introduced to complete finished product processing, backorders, and
                final MO completion in a separate step.
            
                This approach provides better operational control for staged production,
                quality verification, warehouse coordination, and shop floor approval
                processes while preserving compatibility with standard Odoo MRP flows
                and inherited module behaviors.
                """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['mrp'],
    'data': [
        'views/mrp_production_views.xml',
    ],
    'installable': True,
    'images': ['static/description/banner.jpg'],
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
