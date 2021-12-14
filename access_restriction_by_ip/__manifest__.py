# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Access Restriction By IP',
    'summary': """User Can Access His Account Only From Specified IP Address""",
    'version': '15.0.1.0.0',
    'description': """User Can Access His Account Only From Specified IP Address""",
    'live_test_url': 'https://youtu.be/nn6dAL6eKPc',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'category': 'Tools',
    'depends': ['base', 'mail'],
    'license': 'AGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'views/allowed_ips_view.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
}

