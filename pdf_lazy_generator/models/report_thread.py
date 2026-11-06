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
import logging
import threading
import time

from odoo import api, models, _
from odoo.modules.registry import Registry

from ..utils import wkhtmltopdf_request

_logger = logging.getLogger(__name__)


class IrActionsReport(models.Model):
    """Extends ir.actions.report to support background PDF generation."""
    _inherit = "ir.actions.report"

    def generate_in_background(self, report_name, docids, request_id=False, tab_id=False):
        """Start PDF generation in a background thread.
        This method creates a new daemon thread that calls
        `_generate_pdf_thread` to render the report PDF without blocking the main user request.
        """
        _logger.info("[PDF Background] Request received for report: %s (docids: %s)", report_name, docids)
        thread = threading.Thread(
            target=self._generate_pdf_thread,
            args=(report_name, docids, None, request_id, tab_id),
        )
        thread.daemon = True
        thread.start()

    def _generate_pdf_thread(self, report_ref, res_ids, data=None, request_id=False, tab_id=False):
        """Generate the PDF in a background thread using a new database cursor,
        create it as an attachment, and send notifications for download and chatter refresh.
        """
        db_name = self.env.cr.dbname
        uid = self.env.uid
        start_time = time.time()
        with Registry(db_name).cursor() as new_cr:
            env = api.Environment(new_cr, uid, {})
            try:
                _logger.info("[PDF Background] Starting generation for docids: %s (Report: %s)", res_ids, report_ref)
                report = env["ir.actions.report"]._get_report_from_name(report_ref)

                # Use wkhtmltopdf_request to provide a mock request for asset loading
                with wkhtmltopdf_request(env):
                    pdf_content, _format = report._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)

                records = env[report.model].browse(res_ids)

                # Build filename and order reference
                if len(res_ids) == 1:
                    record_name = (records.display_name or _("Document")) if records else _("Document")
                    clean_name = record_name.replace("/", "_").replace("\\", "_")
                    model_desc = env["ir.model"]._get(report.model).name or _("Document")
                    if report.model == "sale.order":
                        model_desc = _("Order")
                    elif report.model == "account.move":
                        model_desc = _("Invoice") if records.move_type == "out_invoice" else _("Document")
                    filename = f"{model_desc} - {clean_name}.pdf"
                    order_ref = record_name
                else:
                    report_title = report.name or _("Report")
                    filename = f"{report_title} - {len(res_ids)} Records.pdf"
                    order_ref = f"{report_title} ({len(res_ids)} records)"

                # Create attachment for download
                attachment = env["ir.attachment"].create({
                    "name": filename,
                    "type": "binary",
                    "datas": base64.b64encode(pdf_content),
                    "res_model": report.model,
                    "res_id": res_ids[0] if res_ids else 0,
                    "mimetype": "application/pdf",
                    "is_background_pdf": True,
                })

                # Attach PDF in chatter if configured
                attach_in_chatter = env["ir.config_parameter"].sudo().get_param(
                    "pdf_lazy_generator.is_attach_pdf_in_chatter"
                )
                if attach_in_chatter == "True":
                    CHATTER_THRESHOLD = 50
                    if len(res_ids) <= CHATTER_THRESHOLD:
                        for record in records:
                            record.with_context(
                                no_new_invoice=True,
                                mail_create_nosubscribe=True,
                            ).message_post(
                                body=_("PDF generated successfully in background."),
                                attachment_ids=[attachment.id],
                            )
                    else:
                        _logger.info(
                            "[PDF Background] Skipping chatter posting for %s records (threshold %s)",
                            len(res_ids),
                            CHATTER_THRESHOLD,
                        )

                # Send download notification (single)
                download_url = f"/web/content/{attachment.id}?download=true"
                env["bus.bus"]._sendone(
                    env.user.partner_id,
                    "pdf_download",
                    {
                        "url": download_url,
                        "name": attachment.name,
                        "order_ref": order_ref,
                        "request_id": request_id,
                        "tab_id": tab_id,
                        "is_attach_pdf_in_chatter": attach_in_chatter == "True",
                    },
                )

                new_cr.commit()
                duration = time.time() - start_time
                _logger.info(
                    "[PDF Background] Successfully generated PDF for report %s in %.2fs",
                    report_ref,
                    duration,
                )
            except Exception as e:
                new_cr.rollback()
                _logger.exception("[PDF Background] Generation failed for report %s", report_ref)
                error_msg = getattr(e, "name", str(e))
                env["bus.bus"]._sendone(
                    env.user.partner_id,
                    "pdf_error",
                    {
                        "message": error_msg,
                        "title": _("PDF Generation Failed"),
                        "tab_id": tab_id,
                    },
                )