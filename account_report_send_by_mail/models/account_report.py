# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana KP (odoo@cybrosys.com)
#
#    This program is under the terms of Odoo Proprietary License v1.0 (OPL-1)
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
################################################################################
import base64
from odoo import models, _


class AccountReport(models.AbstractModel):
    _inherit = "account.report"

    def _get_reports_buttons(self, options):
        """
        This method extends the _init_options_buttons method and adds a
        'Send Mail' button.
        """
        res = super(AccountReport, self)._get_reports_buttons(options)
        res.append(
            {"name": _("Send Mail"), "sequence": 100, "action": "open_send_mail_wizard"})
        return res

    def open_send_mail_wizard(self, options):
        """ Open the send mail wizard to email the accounting report.
        This method generates a PDF of the accounting report and attaches it to
        an email ready for sending.
        Args:
           options (dict): Dictionary containing options for generating the
           report.
        Returns:
           dict: Dictionary containing action information to open the send mail
           wizard. """
        file_content = self.get_pdf(options)
        attachment_values = {
            "name": f"""{self._get_report_name()}.pdf""",
            "type": "binary",
            "datas": base64.b64encode(file_content),
            "mimetype": "application/pdf",
        }
        attachment = self.env["ir.attachment"].sudo().create([attachment_values])
        return {
            "type": "ir.actions.act_window",
            "name": _("Send Mail"),
            "res_model": "send.mail.report",
            "views": [[False, "form"]],
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_subject": "Accounting Report",
                "default_attachment_ids": [attachment.id],
            },
        }
