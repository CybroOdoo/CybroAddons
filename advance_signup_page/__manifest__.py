# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Amal Varghese, Jumana Jabin MP (odoo@cybrosys.com)
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
###############################################################################
{
    'name': "Advance Signup Page",
    'version': '16.0.1.0.0',
    'category': 'Website',
    'summary': """The user can design a more creative and distinctive sign-up
     page for their Odoo website by using Odoo Advance Sign Up.""",
    'description': """The user may create the Sign-Up page for their Odoo
     website using the Odoo Advance Sign Up tool.Various dynamic fields can 
     be added by the Odoo admin as needed to the signup form.The website page
     for signup, login, and password reset can have custom background picture
     selected by the Odoo admin.Admins may also add content to the login, 
     register, and reset password pages from the Odoo backend.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website', 'auth_signup'],
    'data': [
        'security/ir.model.access.csv',
        'views/signup_configuration_views.xml',
        'views/signup_fields_views.xml',
        'views/auth_signup_templates.xml'
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
