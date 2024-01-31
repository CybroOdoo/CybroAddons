# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Akhil Ashok @cybrosys(odoo@cybrosys.com)
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
    'name': 'Upload Multiple Attachments From Tree View',
    'version': "17.0.1.0.0",
    'category': 'Extra Tools',
    'summary': """This module enables users to upload and organize
     multiple documents directly from the tree view.""",
    'description': """This module facilitates the seamless uploading of multiple 
    documents directly from the tree view.Users can easily manage and organize 
    their documents""",
    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'maintainer': "Cybrosys Techno Solutions",
    'website': "https://www.cybrosys.com",
    'depends': ['base'],
    'data': ['security/ir.model.access.csv'],
    'assets': {
        'web.assets_backend': [
            'upload_multi_document/static/src/js/document_multi_upload.js',
            'upload_multi_document/static/src/xml/document_multi_upload.xml'],
    },
    'images': ['static/description/banner.jpg'],
    'license': "AGPL-3",
    'installable': True,
    'auto_install': False,
    'application': False
}
