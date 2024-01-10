# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Abhin K(odoo@cybrosys.com)
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
from ast import literal_eval
from odoo.http import Controller, request, route


class PurchaseFormatEditor(Controller):
    """The PurchaseFormatEditor class provides the functionality to
    download the preview of PDF"""

    @route('/purchase/pdf/preview', type="http", auth="public",
           website=True)
    def purchase_pdf_preview(self):
        """Then demo pdfs are downloaded using this controller.
        The html file from the preview compute field is then converted into
        binary pdf and then returns a response to download it"""
        value = literal_eval(request.params['params'])
        base_doc_layout = request.env['base.document.layout'].sudo().browse(
            value)
        pdf_data = request.env['ir.actions.report'].sudo()._run_wkhtmltopdf(
            [base_doc_layout.preview])
        filename = (f'{base_doc_layout.base_layout_purchase} '
                    f'{base_doc_layout.document_layout_purchase_id.name}.pdf')
        headers = [('Content-Type', 'application/pdf'),
                   ('Content-Disposition',
                    f'attachment; filename="{filename}"')]
        # Send the PDF content as a response with the headers
        return request.make_response(pdf_data, headers=headers)
