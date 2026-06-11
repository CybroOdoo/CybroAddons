# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import threading
import base64
import traceback
from odoo import models, api
from odoo.modules.registry import Registry
import logging
from ..utils import wkhtmltopdf_request

_logger = logging.getLogger(__name__)


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def generate_in_background(self, report_name, docids, data=None, request_id=False, tab_id=False, context=None):
        """
            Start PDF generation in a background thread.
            This method creates a new daemon thread that calls
            `_generate_pdf_thread` to render the report PDF
            without blocking the main user request.
         """
        if tab_id:
            self.env['bus.bus']._sendone(
                self.env.user.partner_id,
                "pdf_started",
                {"tab_id": tab_id}
            )

        try:
            from odoo.http import request
            session_id = request.session.sid if request else False
        except Exception:
            session_id = False

        thread = threading.Thread(
            target=self._generate_pdf_thread,
            args=(report_name, docids, data, request_id, tab_id, context, session_id),
        )
        thread.daemon = True
        thread.start()

    def _build_wkhtmltopdf_args(self, *args, **kwargs):
        command_args = super()._build_wkhtmltopdf_args(*args, **kwargs)
        bg_session_id = self.env.context.get('background_session_id')
        if bg_session_id:
            try:
                command_args.extend(['--cookie', 'session_id', bg_session_id])
            except Exception:
                pass
        return command_args

    def _generate_pdf_thread(self, report_ref, res_ids, data=None, request_id=False, tab_id=False, context=None, session_id=False):
        """
            Generate the PDF in a background thread using a new database cursor,
            create it as an attachment, and send a notification for download.
        """
        db_name = self.env.cr.dbname
        uid = self.env.uid

        with Registry(db_name).cursor() as new_cr:
            env = api.Environment(new_cr, uid, context or {})
            if session_id:
                env = env(context=dict(env.context, background_session_id=session_id))

            try:
                report = env['ir.actions.report']._get_report_from_name(report_ref)

                # Ensure wkhtmltopdf gets a session cookie jar so it can load
                # `/web/assets` even when `dbfilter` is not configured.
                with wkhtmltopdf_request(env):
                    pdf_content, _ = report._render_qweb_pdf(
                        report_ref,
                        res_ids=res_ids,
                        data=data,
                    )

                records = env[report.model].browse(res_ids).exists()
                
                # We only need to create ONE attachment and send ONE download notification 
                # per report generation, even if multiple docids were passed.
                # Usually, one PDF contains all requested labels.
                
                attachment = False
                filename = "Report.pdf"
                record_name = "Document"
                
                if records:
                    # Use the first valid record for naming/metadata
                    target_record = records[0]
                    record_name = target_record.name or "Document"
                    if record_name == "/":
                        record_name = "Draft"
                    
                    clean_name = record_name.replace("/", "_")
                    filename = f"{clean_name}.pdf"
                    
                    if target_record._name == "sale.order":
                        filename = f"Order - {clean_name}.pdf"
                
                # Create the attachment
                attachment = env['ir.attachment'].create({
                    'name': filename,
                    'type': 'binary',
                    'datas': base64.b64encode(pdf_content),
                    'res_model': report.model,
                    'res_id': records[0].id if records else False,
                    'mimetype': 'application/pdf',
                    'is_background_pdf': True,
                })

                # Optional: Post to chatter if config enabled and we have records
                attach_in_chatter = env['ir.config_parameter'].sudo().get_param(
                    'custom_report.is_attach_pdf_in_chatter'
                )
                if attach_in_chatter == 'True' and records:
                    for record in records:
                        try:
                            record.message_post(
                                body="PDF generated successfully.",
                                attachment_ids=[attachment.id],
                            )
                        except Exception:
                            _logger.warning("Failed to post message to chatter for %s(%s)", record._name, record.id)

                # Send SINGLE download notification
                download_url = f"/web/content/{attachment.id}?download=true"
                env['bus.bus']._sendone(
                    env.user.partner_id,
                    "pdf_download",
                    {
                        "url": download_url,
                        "name": attachment.name,
                        "order_ref": record_name,
                        "request_id": request_id,
                        "tab_id": tab_id,
                        "is_attach_pdf_in_chatter": attach_in_chatter == 'True',
                    }
                )
                new_cr.commit()



            except Exception as e:
                new_cr.rollback()
                _logger.error("Background PDF generation failed:\n%s", traceback.format_exc())
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
