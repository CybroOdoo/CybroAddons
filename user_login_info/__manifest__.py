# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu KP (<https://www.cybrosys.com>)
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
    "name": "Login User Info Using Camera",
    "version": "16.0.1.0.0",
    "summary": "Login user information including images date and time will "
    "collect the module using system camera",
    "description": "System capture images of the user when they trying to login"
    " and save into for the future usage"
    "it will include information of log in date and time",
    "category": "Extra Tools",
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": ["account"],
    "data": ["security/ir.model.access.csv", "views/user_log_views.xml"],
    "external_dependencies": {"python": ["cv2"]},
    "license": "LGPL-3",
    "images": ["static/description/banner.jpg"],
    "installable": True,
    "auto_install": False,
    "application": True,
}
