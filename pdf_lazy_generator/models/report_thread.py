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
import threading
import base64
from odoo import models, api
from odoo.modules.registry import Registry
from odoo.addons.mail.tools.discuss import Store

from ..utils import wkhtmltopdf_request


class IrActionsReport(models.Model):
    """
        Extends ir.actions.report to support background PDF generation.
    """
    _inherit = "ir.actions.report"

    def generate_in_background(self, report_name, docids, request_id=False, tab_id=False):
        """
               Start PDF generation in a background thread.
               This method creates a new daemon thread that calls
               `_generate_pdf_thread` to render the report PDF
               without blocking the main user request.
        """
        try:
            from odoo.http import request
            session_id = request.session.sid if request else False
        except Exception:
            session_id = False

        thread = threading.Thread(
            target=self._generate_pdf_thread,
            args=(report_name, docids, None, request_id, tab_id, session_id),
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

    def _generate_pdf_thread(self, report_ref, res_ids, data=None, request_id=False, tab_id=False, session_id=False):
        """
        Generate the PDF in a background thread using a new database cursor,
        create it as an attachment, and send a notification for download.
        """
        db_name = self.env.cr.dbname
        uid = self.env.uid

        with Registry(db_name).cursor() as new_cr:
            env = api.Environment(new_cr, uid, {})
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

                records = env[report.model].browse(res_ids)

                # Determine a filename for the consolidated report
                if len(records) > 1:
                    filename = f"{report.name or 'Report'}.pdf"
                elif records:
                    record = records[0]
                    record_name = record.name or "Draft"
                    clean_name = record_name.replace("/", "_")
                    if record._name == "sale.order":
                        filename = f"Order - {clean_name}.pdf"
                    elif record._name == "account.move":
                        filename = f"{clean_name}.pdf"
                    else:
                        filename = f"{clean_name}.pdf"
                else:
                    filename = "Report.pdf"

                # Create a primary attachment for the download notification
                # We'll use the result of the first record as the 'main' reference if needed,
                # but usually for batch it's better to just use a general name.
                main_record = records[0] if records else None

                attachment = env['ir.attachment'].create({
                    'name': filename,
                    'type': 'binary',
                    'datas': base64.b64encode(pdf_content),
                    'res_model': report.model,
                    'res_id': main_record.id if main_record else 0,
                    'mimetype': 'application/pdf',
                    "is_background_pdf": True
                })

                # If "Attach PDF in Chatter" is enabled, attach to each record
                attach_in_chatter = env['ir.config_parameter'].sudo().get_param(
                    'custom_report.is_attach_pdf_in_chatter'
                )

                try:
                    # Get the current user's partner_id for targeted notification
                    user_partner_id = env.user.partner_id.id

                    for record in records:
                        message = False
                        if attach_in_chatter == 'True':
                            message = record.message_post(
                                body="PDF generated successfully.",
                                attachment_ids=[attachment.id],
                                subtype_xmlid='mail.mt_comment',
                                partner_ids=[user_partner_id],
                            )

                        # Commit here ensures message and attachment are in DB
                        new_cr.commit()

                        # Send bus notification to refresh chatter
                        # 1. Notify current user's partner channel
                        try:
                            store_user = Store(bus_channel=env.user.partner_id)
                            if message:
                                store_user.add(message)
                            store_user.add(record, [], as_thread=True, request_list=["attachments", "messages"])
                            store_user.bus_send()
                        except:
                            pass

                        # 2. Notify thread channel (standard for chatter updates)
                        try:
                            store_thread = Store(bus_channel=record)
                            if message:
                                store_thread.add(message)
                            store_thread.add(record, [], as_thread=True, request_list=["attachments", "messages"])
                            store_thread.bus_send()
                        except:
                            pass
                except Exception as store_error:
                    # Log the error but don't fail the PDF generation
                    env['ir.logging'].sudo().create({
                        'name': 'pdf_lazy_generator',
                        'type': 'server',
                        'level': 'error',
                        'dbname': env.cr.dbname,
                        'path': __file__,
                        'line': '0',
                        'msg': str(store_error),
                    })
                
                # Final commit before bus notification
                new_cr.commit()

                # Send download notification with metadata
                env['bus.bus']._sendone(
                    env.user.partner_id,
                    "pdf_download",
                    {
                        "url": f"/web/content/{attachment.id}?download=true",
                        "name": attachment.name,
                        "order_ref": attachment.name.replace(".pdf", ""),
                        "res_ids": res_ids,
                        "model": report.model,
                        "tab_id": tab_id,
                        "message_id": message.id if message else False,
                        "attachment_id": attachment.id,
                        "is_attach_pdf_in_chatter": attach_in_chatter == 'True',
                    }
                )

            except Exception as e:
                new_cr.rollback()
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
