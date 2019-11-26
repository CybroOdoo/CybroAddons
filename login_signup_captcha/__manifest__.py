# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Login/signup reCAPTCHA',
    'version': '12.0.1.0.0',
    'summary': """Protect robot login and signup with reCAPTCHA""",
    'description': """CAPTCHA helps you detect abusive traffic on your website without any user friction. 
    The user must register their  domain with CAPTCHA site to get site key add same with our code and use the app.
    login page, signup page,login,signup,protection,site protection,fake login,fake signup,website login, 
    website,captcha,captcha,version 12 protectionwebsite protection,robot attack,security,secure login
    ,secure signup""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'category': 'Extra Tools',
    'depends': ['base'],
    'images': ['static/description/banner.gif'],
    'license': 'LGPL-3',
    'depends': ['base','web'],
    'data': ['views/captcha_views.xml'],
    'installable': True,
    'auto_install': False,

}