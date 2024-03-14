# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies(odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
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
from datetime import datetime
try:
    from BytesIO import BytesIO
except ImportError:
    from io import BytesIO
import zipfile
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
                ('Content-Type', 'application/x-zip-compressed'),
                ('Content-Disposition', content_disposition(zip_filename))])
