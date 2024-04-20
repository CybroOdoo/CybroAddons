# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohammed Dilshad Tk (odoo@cybrosys.com)
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
import logging
try:
    from BytesIO import BytesIO
except ImportError:
    from io import BytesIO
import zipfile
from datetime import datetime
from odoo import http
from odoo.http import request
from odoo.http import content_disposition
import ast

_logger = logging.getLogger(__name__)


class Binary(http.Controller):
    """Attachment downloading binary class"""

    @http.route('/web/binary/download_document', type='http',
                auth="public")
    def download_document(self, tab_id):
        """Download attachment method"""
        new_tab = ast.literal_eval(tab_id)
        attachment_ids = request.env['ir.attachment'].browse(new_tab)
        file_dict = {}
        for attachment_id in attachment_ids:
            file_store = attachment_id.store_fname
            if file_store:
                file_name = attachment_id.name
                file_path = attachment_id._full_path(file_store)
                file_dict["%s:%s" % (file_store, file_name)] = dict(
                    path=file_path, name=file_name)
        zip_filename = datetime.now()
        zip_filename = "%s.zip" % zip_filename
        bitIO = BytesIO()
        zip_file = zipfile.ZipFile(bitIO, "w", zipfile.ZIP_DEFLATED)
        for file_info in file_dict.values():
            zip_file.write(file_info["path"], file_info["name"])
        zip_file.close()
        return request.make_response(bitIO.getvalue(),
                                     headers=[('Content-Type',
                                               'application/x-zip-compressed'),
                                              ('Content-Disposition',
                                               content_disposition(
                                                   zip_filename))]
                                     )
