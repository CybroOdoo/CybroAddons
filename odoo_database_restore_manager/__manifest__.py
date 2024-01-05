# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aslam AK (odoo@cybrosys.com)
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
    'name': "Database Restore Manager Odoo16",
    'version': "16.0.1.0.0'",
    'category': "Extra Tools",
    'summary': """Easily Restore The Previous Database Backups Stored in Different Locations like Google Drive,
                    Dropbox, Onedrive, Nextcloud and Amazon S3""",
    'description': """TEasily Restore The Previous Database Backups Stored in Different Locations like Google Drive,
                    Dropbox, Onedrive, Nextcloud and Amazon S3, backup, automatic backup""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base_setup', 'auto_database_backup'],
    'data': [
        'security/ir.model.access.csv',
        'views/database_manager_views.xml',
        'views/res_config_settings_views.xml',
        'wizard/database_restore_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            '/odoo_database_restore_manager/static/src/js/db_restore.js',
            '/odoo_database_restore_manager/static/src/xml/db_restore_dashboard_templates.xml',
            '/odoo_database_restore_manager/static/src/scss/db_restore.scss'
        ]
    },
    'external_dependencies': {'python': ['dropbox', 'gdown']},
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
