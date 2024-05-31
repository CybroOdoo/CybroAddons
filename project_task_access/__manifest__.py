# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (<https://www.cybrosys.com>)
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
    "name": "Users Restriction For Project And Task",
    "version": "17.0.1.0.0",
    "category": "Project",
    "summary": "Users Restriction For Project And Task restricts and access "
    "the users to the project and task records.",
    "description": """The 'Users Restriction For Project And Task' is a system 
    designed to specify and control which individuals or roles within an 
    organization have permission to view or interact with project and task 
    records. It ensures that only authorized users can access and manage 
    sensitive project and task-related information, enhancing security and 
    privacy within the organization's data management processes""",
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": ["project"],
    "data": [
        "security/project_task_security.xml",
        "views/project_project_views.xml",
        "views/project_task_views.xml",
    ],
    "images": ["static/description/banner.jpg"],
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
}
