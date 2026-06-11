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
import io
import logging
from odoo import models
from odoo.tools import pdf
from odoo.tools.pdf import PdfFileWriter

# Import the specific class to call super on it, bypassing the buggy immediate parent if needed
# But here we inherit from it to override it.
from odoo.addons.sale_pdf_quote_builder.models.ir_actions_report import IrActionsReport as SalePdfIrActionsReport

_logger = logging.getLogger(__name__)

class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf_prepare_streams(self, report_ref, data, res_ids=None):
        # Call super of the parent class (SalePdfIrActionsReport) to skip its implementation
        # and get the original stream from base/account if possible, OR re-implement the logic safely.
        # Actually, since we want to fix the logic inside SalePdfIrActionsReport, we should replicate it
        # but with a try-except block around the failing line.
        
        # We first call the implementation *before* sale_pdf_quote_builder to get the raw streams.
        # Since we cannot easily skip one level of MRO, we will assume we want to fix the logic.
        # However, calling super() here calls SalePdfIrActionsReport._render... which crashes.
        # So we need to call the super of SalePdfIrActionsReport directly!
        
        # Get the original result (from account/base)
        result = super(SalePdfIrActionsReport, self)._render_qweb_pdf_prepare_streams(report_ref, data, res_ids=res_ids)
        
        if self._get_report(report_ref).report_name != 'sale.report_saleorder':
            return result

        # NOW re-implement the logic from sale_pdf_quote_builder safely
        orders = self.env['sale.order'].browse(res_ids)

        for order in orders:
            initial_stream = result[order.id]['stream']
            if initial_stream:
                order_template = order.sale_order_template_id
                header_record = order_template if order_template.sale_header else order.company_id
                footer_record = order_template if order_template.sale_footer else order.company_id
                has_header = bool(header_record.sale_header)
                has_footer = bool(footer_record.sale_footer)
                included_product_docs = self.env['product.document']
                doc_line_id_mapping = {}
                for line in order.order_line:
                    product_product_docs = line.product_id.product_document_ids
                    product_template_docs = line.product_template_id.product_document_ids
                    doc_to_include = (
                        product_product_docs.filtered(lambda d: d.attached_on == 'inside')
                        or product_template_docs.filtered(lambda d: d.attached_on == 'inside')
                    )
                    included_product_docs = included_product_docs | doc_to_include
                    doc_line_id_mapping.update({doc.id: line.id for doc in doc_to_include})

                if (not has_header and not included_product_docs and not has_footer):
                    continue

                writer = PdfFileWriter()
                if has_header:
                    self._add_pages_to_writer(writer, base64.b64decode(header_record.sale_header))
                if included_product_docs:
                    for doc in included_product_docs:
                        self._add_pages_to_writer(
                            writer, base64.b64decode(doc.datas), doc_line_id_mapping[doc.id]
                        )
                self._add_pages_to_writer(writer, initial_stream.getvalue())
                if has_footer:
                    self._add_pages_to_writer(writer, base64.b64decode(footer_record.sale_footer))

                form_fields = self._get_form_fields_mapping(order, doc_line_id_mapping)
                
                # THIS IS THE FIX: Try/Except block
                try:
                    pdf.fill_form_fields_pdf(writer, form_fields=form_fields)
                except Exception as e:
                    _logger.warning(f"Could not fill form fields in PDF for order {order.name}: {e}")
                    # If filling fails, we proceed with the writer as is (fields won't be filled)

                with io.BytesIO() as _buffer:
                    writer.write(_buffer)
                    stream = io.BytesIO(_buffer.getvalue())
                result[order.id].update({'stream': stream})

        return result
