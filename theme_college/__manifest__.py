# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    "name": "Theme College",
    "version": "14.0.1.0.0",
    "category": "Theme/Education",
    "summary": "Theme College is a new kind of Theme. The theme is a very "
               "user-friendly and is suitable for your"
               " educational institutions website.",
    "description": """
        It is the most powerful, easy to use theme with Front-end styles.
        Carousel slide, College location, Placement cell and Scholarship 
        form snippets facilitates to add better user experience.
        Contains Custom Pages including Courses, Facilities, Gallery, Alumni.
        It has Image Viewer on Gallery.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    "website": "https://www.cybrosys.com",
    "depends": [
        'base',
        'web',
        'website',
        'website_livechat',
        'website_form',
    ],
    'images': [
        'static/description/banner.png',
        'static/description/hero.png',
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/college_location_views.xml',
        'views/theme_college_menus.xml',
        'views/website_templates.xml',
        'views/theme_college_templates.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
