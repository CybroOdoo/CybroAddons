# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra MP (odoo@cybrosys.com)
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
import base64
from odoo import models


class MailTemplate(models.Model):
    """Inherit the class to send mail to all product documents."""
    _inherit = "mail.template"

    def generate_email(self, res_ids, fields):
        """Super the function generate_email to add product documents in mail"""
        res = super(MailTemplate, self).generate_email(res_ids, fields)
        if self.render_model == 'purchase.order':
            documents = []
            for document_id in self.env['purchase.order'].browse(
                res_ids[0]).order_line.document_ids:
                documents.append(
                    (document_id.name, base64.b64encode(document_id.raw)))
            res[res_ids[0]]['attachments'] += documents
        return res
