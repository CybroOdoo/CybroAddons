# -*- coding: utf-8 -*-

##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2012-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
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
    'name': "Quality Control - Multiple Quantitative Values",
    'version': "8.0.1.0.0",
    'category': "Quality control",
    'summary': 'Quality Control - Multiple Quantitative Values With Different Statistical Averaging Methods.',
    'description': """
    Manage the Quality Control process with Multiple Quantitative Values
    ====================================================================
    This module allows you to give multiple quantitative values in the quality control lines as the result.
    Also we can mention the calculation method in the line like Mean,Mode,Median,Largest and smallest.
    the result(Quantitative value) will calculated automatically.
    -------------------------------------------------------------------------------------------------
    * Allows to manage Multiple Quantitative Values
    * We can set the Number of tests and calculation method
    * Different calculation methods - Mean,Mode,Median,Largest and smallest
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['product', 'quality_control'],
    'data': ['views/qc_inspection_views.xml'],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    # install sudo pip install statistics
}
