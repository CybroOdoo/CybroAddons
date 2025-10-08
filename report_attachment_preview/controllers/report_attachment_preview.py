# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana KP (Contact : odoo@cybrosys.com)
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
from odoo import http
from odoo.addons.web.controllers.binary import Binary as BaseBinary


class CustomBinary(BaseBinary):
    """ This controller extends the base Binary controller to customize the
    behavior of serving binary content such as PDF reports and attachments."""

    @http.route()
    def content_common(self, xmlid=None, model='ir.attachment', id=None,
                       field='raw',
                       filename=None, filename_field='name', mimetype=None,
                       unique=False,
                       download=False, access_token=None, nocache=False):
        """ This method overrides the base content_common method to provide custom
        handling for serving binary content. It ensures that binary content, such
        as PDF reports and attachments, is viewed in a new browser tab without
        downloading it. """
        res = super().content_common(xmlid, model, id, field,
                       filename, filename_field, mimetype, unique,
                       download, access_token, nocache)

        record = http.request.env['ir.binary']._find_record(xmlid, model, id and int(id), access_token)
        res.headers[
                'Content-Disposition'] = "inline; filename=%s" % record.name
        return res
