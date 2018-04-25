# -*- coding: utf-8 -*-
###################################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Saritha Sahadevan (<https://www.cybrosys.com>)
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
    'name': "Open HRMS Employee Appraisal",
    'version': '11.0.1.0.0',
    'summary': """Roll out appraisal plans and get the best of your workforce""",
    'description': """Roll out appraisal plans and get the best of your workforce""",
    'category': 'Human Resources',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.openhrms.com",
    'depends': ['base', 'hr', 'survey'],
    'data': [
        'security/ir.model.access.csv',
        'security/hr_appraisal_security.xml',
        'views/hr_appraisal_survey_views.xml',
        'views/hr_appraisal_form_view.xml',
        'data/hr_appraisal_stages.xml'
    ],
    'images': ["static/description/banner.jpg"],
    'license': "AGPL-3",
    'installable': True,
    'application': False,
}
