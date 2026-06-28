# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import base64
import threading
import logging

from odoo import api, models
from odoo.modules.registry import Registry

from ..utils import wkhtmltopdf_request


_logger = logging.getLogger(__name__)


class AccountReport(models.Model):
    """
        Extends account.report to support background PDF generation.
    """
    _inherit = "account.report"

    def generate_in_background(self, options, request_id=False, tab_id=False):
        """
        Start enterprise accounting report PDF generation in a background thread.
        `options` is the full options dict passed from the JS frontend —
        it contains report_id, date_from, date_to, comparison, filters, etc.
        """
        # Propagate context so the background render uses the same company/lang/etc.
        ctx = dict(self.env.context)
        thread = threading.Thread(
            target=self._generate_pdf_thread,
            args=(options, request_id, tab_id, ctx),
        )
        thread.daemon = True
        thread.start()

    def _generate_pdf_thread(self, options, request_id=False, tab_id=False, context=None):
        """
        Generate the accounting report PDF in a background thread.
        Uses a fresh DB cursor, creates an ir.attachment, and
        pushes a bus notification so the frontend can download it.
        """
        db_name = self.env.cr.dbname
        uid = self.env.uid
        report_id = options.get("report_id")

        with Registry(db_name).cursor() as new_cr:
            env = api.Environment(new_cr, uid, context or {})
            try:
                report = env["account.report"].browse(report_id)

                if not report.exists():
                    _logger.error(
                        "Background accounting PDF: account.report id=%s not found.", report_id
                    )
                    return


                with wkhtmltopdf_request(env):
                    pdf_content = report.export_to_pdf(options)['file_content']

                report_name = report.name or "Report"
                date_to = (options.get("date", {}) or {}).get("date_to", "")
                clean_name = report_name.replace("/", "_")
                filename = f"{clean_name}{(' - ' + date_to) if date_to else ''}.pdf"

                attachment = env["ir.attachment"].create(
                    {
                        "name": filename,
                        "type": "binary",
                        "datas": base64.b64encode(pdf_content),
                        "res_model": "account.report",
                        "res_id": report.id,
                        "mimetype": "application/pdf",
                        "is_background_pdf": True,
                    }
                )

                download_url = f"/web/content/{attachment.id}?download=true"

                new_cr.commit()
                env["bus.bus"]._sendone(
                    env.user.partner_id,
                    "pdf_download",
                    {
                        "url": download_url,
                        "name": filename,
                        "order_ref": report_name,
                        "request_id": request_id,
                        "tab_id": tab_id,
                    },
                )
                _logger.info("Background accounting PDF generated: %s", filename)

            except Exception as e:
                new_cr.rollback()
                _logger.exception(
                    "Background accounting PDF generation failed for report_id=%s", report_id
                )
                error_msg = str(e)
                if hasattr(e, 'name'):
                    error_msg = e.name
                
                env['bus.bus']._sendone(
                    env.user.partner_id,
                    "pdf_error",
                    {
                        "message": error_msg,
                        "title": "PDF Generation Failed",
                        "tab_id": tab_id,
                    }
                )
