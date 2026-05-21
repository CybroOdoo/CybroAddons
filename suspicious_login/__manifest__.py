# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V (odoo@cybrosys.com)
#
#   This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
{
    'name': '2FA Login with Email OTP',
    'version': '17.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'The module aims to prevent suspicious login attempts by '
               'implementing additional security measures in the login '
               'process.',
    'description': """The "2FA Login with Email OTP" module is 
    designed to enhance the security of the login process in Odoo.
    It provides a set of features to prevent and detect suspicious 
    login attempts, thereby protecting the system from unauthorized 
    access.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['web_unsplash','website', 'mail'],
    'data': [
        'security/suspicious_login_security.xml',
        'security/ir.model.access.csv',
        'data/mail_data.xml',
        'views/res_users_login_attempt_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/suspicious_login/static/src/js/list_render_login.js',
            'suspicious_login/static/src/css/login.css',
        ],
        'web.assets_frontend': [
            'suspicious_login/static/src/js/login.js',
        ]
    },
    'images': ['static/description/banner.jpg'],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': False
}
