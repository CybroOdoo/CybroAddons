# -*- coding: utf-8 -*-

##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2009-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nikhil krishnan(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

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
    'version': '8.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Secondary UoM in Manufacturing order',
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
    'website': "http://www.yourcompany.com",
    'company': 'Cybrosys Techno Solutions',
    'depends': ['mrp'],
    'data': ['views/mrp_sec_uom.xml'],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
}
