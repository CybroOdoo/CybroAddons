# -*- coding: utf-8 -*-
###############################################################################
#
#  Cybrosys Technologies Pvt. Ltd.
#
#  Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#  Author: Anusha C (odoo@cybrosys.com)
#
#  You can modify it under the terms of the GNU LESSER
#  GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#  You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#  (LGPL v3) along with this program.
#  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    "name": "HR Holiday Generator",
    "version": "16.0.1.0.0",
    "category": 'Human Resources',
    "summary": """Generate public holidays based on selected criteria.""",
    "description": """This module allows you to generate public holidays based 
    on selected criteria such as year, month, or a specific date.It provides a 
    wizard that communicates with an external API to fetch public holiday data 
    and create corresponding calendar leaves.You can customize the criteria and 
    view the generated holidays within the wizard itself.""",
    "author": "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    "depends": ["hr_holidays"],
    "data": ["security/ir.model.access.csv",
             "views/res_config_settings_views.xml",
             "views/holiday_log_views.xml",
             "wizard/overlapping_date_views.xml",
             "wizard/hr_holiday_generator_views.xml",
             "wizard/calendar_leave_generator_views.xml"],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
