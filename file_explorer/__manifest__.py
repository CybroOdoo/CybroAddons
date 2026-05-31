# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Afthab K Naufal @cybrosys (odoo@cybrosys.com)
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
    'name':'File Explorer',
    'version':'17.0.1.0.0',
    'summary': 'To Upload to server and Download file from remote',
    'description': "FileExplorer can be used to connect to remote and can "
                   "upload file to remote or can download file "
                   "from the remote",
    'category': 'Extra Tools',
    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'maintainer': "Cybrosys Techno Solutions",
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'website', 'board'],
    'data':
    [
        'views/file_explorer_view.xml',
    ],
    'assets':
            {
                'web.assets_backend':[
                    'file_explorer/static/src/css/upload_file.css',
                    'file_explorer/static/src/js/upload_file.js',
                    'file_explorer/static/src/xml/upload_file.xml',
                    'file_explorer/static/src/css/file_explorer.css',
                    'file_explorer/static/src/js/file_explorer.js',
                    'file_explorer/static/src/xml/file_explorer.xml',
                ],
            },
    'images': ['static/description/banner.jpg'],
    'license':'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
 }
