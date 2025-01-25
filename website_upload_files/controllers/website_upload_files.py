# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
import base64
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers import main


class WebsiteSaleFileUpload(main.WebsiteSale):
    """For attaching the file in website sale order"""
    @http.route()
    def shop_payment(self, **post):
        res = super(WebsiteSaleFileUpload, self).shop_payment(**post)
        order = res.qcontext['order']
        if post.get('attachment'):
            if post.get('attachment', False):
                file = post.get('attachment')
                request.env['ir.attachment'].sudo().create({
                    'name': post.get('attachment').filename,
                    'res_name': post.get('attachment').filename,
                    'type': 'binary',
                    'res_model': 'sale.order',
                    'res_id': order.id,
                    'datas': base64.b64encode(file.read()),
                })
        all_attachments = request.env['ir.attachment'].search(
            [('res_model', '=', 'sale.order'), ('res_id', '=', order.id)])
        res.qcontext.update({'attachment': all_attachments})
        return res

    @http.route('/shop/attachments', type='json', auth='public', website=True,
                sitemap=False)
    def shop_attachments(self, **post):
        """For delete the attachment from websites"""
        attachment = request.env['ir.attachment'].sudo().browse(int(post.get(
            "attachment_id")))
        attachment.unlink()
        return 1
