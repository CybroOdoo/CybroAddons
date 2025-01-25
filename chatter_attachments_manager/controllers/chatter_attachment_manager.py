# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nikhil M (odoo@cybrosys.com)
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
################################################################################
import zipfile
from datetime import datetime

try:
    from BytesIO import BytesIO
except ImportError:
    from io import BytesIO

from odoo import http
from odoo.http import request, content_disposition

class Binary(http.Controller):
    """Attachment downloading binary class."""

    @http.route('/web/binary/download_document', type='http',
                auth='public')
    def download_zip(self, **kwargs):
        """This method used to download all chatter attachments inside a record
        as a zip file."""
        model = kwargs.get('param1', 0)
        tab_id = int(kwargs.get('param2', 0))
        attachment_ids = request.env['ir.attachment'].search(
            [('res_model', '=', model), ('res_id', '=', tab_id)])
        file_dict = {}
        for attachment_id in attachment_ids:
            file_store = attachment_id.store_fname
            if file_store:
                file_name = attachment_id.name
                file_path = attachment_id._full_path(file_store)
                file_dict[f"{file_store}:{file_name}"] = {
                    'path': file_path, 'name': file_name}
        zip_filename = datetime.now()
        zip_filename = f"{zip_filename}.zip"
        bit_io = BytesIO()
        with zipfile.ZipFile(bit_io, "w",
                             zipfile.ZIP_DEFLATED) as zip_file:
            for file_info in file_dict.values():
                zip_file.write(file_info["path"], file_info["name"])
            zip_file.close()
            return request.make_response(bit_io.getvalue(), headers=[
                ('Content-Type', 'application/zip'),
                ('Content-Disposition', http.content_disposition(zip_filename))])