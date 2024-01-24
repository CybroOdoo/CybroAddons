# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from odoo import models


class MailTemplate(models.Model):
    """Inherit the class to send mail to all product attachments."""
    _inherit = "mail.template"

    def _generate_template_attachments(self, res_ids, render_fields,
                                       render_results=None):
        """Super the function generate_email to add product attachments in
        mail"""
        res = super(MailTemplate, self)._generate_template_attachments(res_ids,
                                                                       render_fields,
                                                                       render_results)
        if self.render_model == 'purchase.order':
            attachments = []
            for attachment_id in self.env['purchase.order'].browse(
                    res_ids[0]).order_line.attachment_ids:
                attachments.append(
                    (attachment_id.name, base64.b64encode(attachment_id.raw)))
            res[res_ids[0]]['attachments'] += attachments
        if self.render_model == 'sale.order':
            attachments = []
            for attachment_id in self.env['sale.order'].browse(
                    res_ids[0]).order_line.attachment_ids:
                attachments.append(
                    (attachment_id.name, base64.b64encode(attachment_id.raw)))
            res[res_ids[0]]['attachments'] += attachments
        return res
