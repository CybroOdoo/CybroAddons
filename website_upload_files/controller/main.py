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

from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request
import base64
from odoo import fields, http, SUPERUSER_ID, tools, _


class WebsiteSaleFileUpload(WebsiteSale):

    @http.route(['/shop/add_attachment'], type='http', auth="public", website=True,
                sitemap=False)
    def add_attachments(self, **post):
        order = request.website.sale_get_order()
        if post.get('attachment', False):
            attachment_ids = request.env['ir.attachment']
            name = post.get('attachment').filename
            file = post.get('attachment')
            attachment = file.read()
            attachment_ids.sudo().create({
                'name': name,
                'res_name': name,
                'type': 'binary',
                'res_model': 'sale.order',
                'res_id': order.id,
                'datas': base64.b64encode(attachment),
            })
