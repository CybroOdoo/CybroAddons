# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swetha Anand (odoo@cybrosys.com)
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
import base64
import logging
import json
import unicodedata

from odoo.exceptions import AccessError
from odoo.http import request
from odoo import _, http
from odoo.addons.web.controllers.main import Binary

_logger = logging.getLogger(__name__)


def clean(name): return name.replace('\x3c', '')


class Binary(Binary):
    """This class is called to override upload_attachment()."""
    @http.route('/web/binary/upload_attachment', type='http', auth="user")
    def upload_attachment(self, model, id, ufile, callback=None):
        """
        Override the function upload_attachment() to include
        a check to see if the size of the attachment exceeds
        the user-assigned maximum size. If true, an error
        message is displayed.
        """
        files = request.httprequest.files.getlist('ufile')
        Model = request.env['ir.attachment']
        out = """<script language="javascript" type="text/javascript">
                       var win = window.top.window;
                       win.jQuery(win).trigger(%s, %s);
                   </script>"""
        args = []
        max_size = request.env.user.max_size * 1024 * 1024
        for ufile in files:
            filename = ufile.filename
            if request.httprequest.user_agent.browser == 'safari':
                # Safari sends NFD UTF-8
                # (where é is composed by 'e' and [accent])
                # we need to send it the same stuff, otherwise it'll fail
                filename = unicodedata.normalize('NFD', ufile.filename)
            try:
                attachment = Model.create({
                    'name': filename,
                    'datas': base64.encodebytes(ufile.read()),
                    'res_model': model,
                    'res_id': int(id)
                })
                attachment._post_add_create()
            except AccessError:
                args.append({'error': _(
                    "You are not allowed to upload an attachment here.")})
            except Exception:
                args.append({'error': _("Something horrible happened")})
                _logger.exception("Fail to upload attachment %s"
                                  % ufile.filename)
            else:
                args.append({
                    'filename': clean(filename),
                    'mimetype': ufile.content_type,
                    'id': attachment.id,
                    'size': attachment.file_size
                })
            for dict in args:
                if dict.get('size'):
                    if dict.get('size') > max_size:
                        args.append({'error': _(
                            'Attachment size cannot exceed %s MB.')
                                              % request.env.user.max_size})
                        attachment.unlink()
        return out % (json.dumps(clean(callback)), json.dumps(
            args)) if callback else json.dumps(args)
