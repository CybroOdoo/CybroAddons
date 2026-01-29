# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mruthul Raj (odoo@cybrosys.com)
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
################################################################################
{
    'name': 'Question Duplicator in Survey',
    'version': '15.0.1.0.0',
    'category': 'Marketing',
    'summary': """This module provides a feature that makes it possible to 
     duplicate survey questions in the Survey module.""",
    'description': """In the Survey module, there is no possibility to 
     duplicate the questions. With the help of this module, users can quickly 
     and easily add the same question to several surveys. Both the list view and
     the form view of the question support duplication. The list view allows 
     for the selection of several questions for duplication, and the duplicated
     questions can then be added to numerous surveys simultaneously.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['survey'],
    'data': [
        'security/ir.model.access.csv',
        'views/survey_question_views.xml',
        'wizard/survey_selector_views.xml'
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
