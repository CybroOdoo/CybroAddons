# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
    'name': 'Camera In Discuss',
    'version': '20.0.1.0.0',
    'summary': 'Capture and send live camera photos directly in Discuss chat',
    'description': """Camera in Discuss enables instant camera photo capture and
    attachment directly inside Odoo Discuss and chat composers.""",
    'category': 'Discuss',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'mail', 'im_livechat'],
    'assets': {
        'web.assets_backend': [
            'camera_in_discuss/static/src/discuss/camera/common/composer_patch.js',
            'camera_in_discuss/static/src/discuss/camera/common/camera.css',
        ],
        'web.assets_frontend': [
            'camera_in_discuss/static/src/discuss/camera/common/composer_patch.js',
            'camera_in_discuss/static/src/discuss/camera/common/camera.css',
        ],
        'im_livechat.assets_embed_core': [
            'camera_in_discuss/static/src/discuss/camera/common/composer_patch.js',
            'camera_in_discuss/static/src/discuss/camera/common/camera.css',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}

