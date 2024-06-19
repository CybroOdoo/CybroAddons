# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Bhagyadev KP (odoo@cybrosys.com)
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
import markupsafe
from odoo import models, _


class AccountReport(models.Model):
    _inherit = "account.report"

    def _init_options_buttons(self, options, previous_options=None):
        """
        This method extends the _init_options_buttons method and adds a
        'Send Mail' button.
        """
        super(AccountReport, self)._init_options_buttons(options, previous_options)
        options["buttons"].append(
            {"name": _("Send Mail"), "sequence": 100, "action": "open_send_mail_wizard"}
        )

    def open_send_mail_wizard(self, options):
        """
        Open the send mail wizard to email the accounting report.

        This method generates a PDF of the accounting report and attaches it to
        an email ready for sending.

        Args:
           options (dict): Dictionary containing options for generating the
           report.

        Returns:
           dict: Dictionary containing action information to open the send mail
           wizard.

        """
        self.ensure_one()
        base_url = self.env["ir.config_parameter"].sudo().get_param(
            "report.url"
        ) or self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        rcontext = {
            "mode": "print",
            "base_url": base_url,
            "company": self.env.company,
        }
        print_mode_self = self.with_context(print_mode=True)
        print_options = print_mode_self._get_options(previous_options=options)
        body_html = print_mode_self.get_html(
            print_options,
            self._filter_out_folded_children(print_mode_self._get_lines(print_options)),
        )
        body = self.env["ir.ui.view"]._render_template(
            "account_reports.print_template",
            values=dict(rcontext, body_html=body_html),
        )
        footer = self.env["ir.actions.report"]._render_template(
            "web.internal_layout", values=rcontext
        )
        footer = self.env["ir.actions.report"]._render_template(
            "web.minimal_layout",
            values=dict(rcontext, subst=True, body=markupsafe.Markup(footer.decode())),
        )
        landscape = False
        if len(print_options["columns"]) * len(print_options["column_groups"]) > 5:
            landscape = True
        file_content = self.env["ir.actions.report"]._run_wkhtmltopdf(
            [body],
            footer=footer.decode(),
            landscape=landscape,
            specific_paperformat_args={
                "data-report-margin-top": 10,
                "data-report-header-spacing": 10,
            },
        )
        attachment_values = {
            "name": f"""{options['available_variants'][0]['name']}.pdf""",
            "type": "binary",
            "datas": base64.b64encode(file_content),
            "mimetype": "application/pdf",
            "res_model": "account.report",
            "res_id": self.id,
        }
        attachment = self.env["ir.attachment"].sudo().create(attachment_values)
        return {
            "type": "ir.actions.act_window",
            "name": _("Send Mail"),
            "res_model": "send.mail.report",
            "views": [[False, "form"]],
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_report_id": self.id,
                "default_subject": "Accounting Report",
                "default_attachment_ids": [attachment.id],
            },
        }
