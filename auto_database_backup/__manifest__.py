# -*- coding: utf-8 -*-
###############################################################################
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
###############################################################################
{
    'name': "Automatic Database Backup To Local Server, Remote Server, Google "
            "Drive, Dropbox, Onedrive, Nextcloud and Amazon S3",
    'version': '15.0.5.1.0',
    'category': 'Discuss,Extra Tools',
    'summary': """Generate automatic backup of databases and store to local,
     google drive, dropbox, nextcloud, amazon S3, onedrive or 
     remote server""",
    'description': """This module helps to generate backups of your databases 
     automatically on regular interval of times. The generated backups can be 
     stored into local storage, ftp server, sftp server, dropbox, Google Drive, 
     Onedrive Nextcloud and Amazon S3. User can enable auto remove option to 
     automatically delete old backups. User can enable email notification to 
     be notified about the success and failure of the backup generation and 
     storage.""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'data/mail_data.xml',
        'views/db_backup_configure_views.xml',
        'wizard/dropbox_auth_code_views.xml',
    ],
    'external_dependencies': {
        'python': ['dropbox', 'pyncclient', 'boto3', 'nextcloud-api-wrapper','paramiko'],
    },
    'images': ['static/description/banner.gif'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
