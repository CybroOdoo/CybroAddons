# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': "Automatic Database Backup To Local Server, Remote Server, Google Drive, Dropbox and Onedrive",
    'version': '16.0.1.0.0',
    'summary': """Generate automatic backup of databases and store to local, google drive, dropbox, onedrive or remote server""",
    'description': """This module has been developed for creating database backups automatically 
                    and store it to the different locations.""",
    'author': "Cybrosys Techno Solutions",
    'website': "https://www.cybrosys.com",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'category': 'Tools',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/db_backup_configure_views.xml',
        'wizard/authentication_wizard_views.xml',
    ],
    'external_dependencies': {'python': ['dropbox']},
    'license': 'LGPL-3',
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
