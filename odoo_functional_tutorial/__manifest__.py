# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Javid A (<https://www.cybrosys.com>)
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
#############################################################################
{
    'name': "Odoo16 Enterprise Functional Tutorial",
    'version': '16.0.1.0.0',
    'category': 'Tutorial',
    'summary': "Functional Tutorial videos for all the modules in odoo16",
    'description': """The eLearning module offers a comprehensive course 
     encompassing all the essential enterprise functions in Odoo 16, providing 
     learners with in-depth tutorials and hands-on training to master the 
     platform's capabilities and optimize their proficiency in utilizing its 
     features for business success""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': "Cybrosys Techno Solutions",
    'website': 'https://www.cybrosys.com',
    'depends': ['website_slides'],
    'data': [
        'data/slide_channel_data.xml',
        'data/slide.slide.csv',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
