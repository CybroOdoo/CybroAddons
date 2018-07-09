# -*- coding: utf-8 -*-

##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nikhil krishnan(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'MRP - Secondary UoM',
    'version': '10.0.1.0',
    'category': 'Manufacturing',
    'summary': 'Secondary UoM in Manufacturing Order',
    'description': """
Manage the Manufacturing process with secondary UoM
===================================================
This module allows you to cover planning, ordering, stocks and the manufacturing with a Secondary UoM. It handles the
Products to Produce & Produced Products according to the production with Secondary UoM
-----------------------------------------------------------------------------------------
* Allows to manage MRP with Secondary UoM
* Products to Produce With Secondary UoM
* Produced Products With Secondary UoM
""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': "http://www.cybrosys.com",
    'depends': ['mrp'],
    'data': ['views/mrp_sec_uom.xml',
             'data/mrp_sec_uom_round.xml'],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}
