# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ammu Raj(odoo@cybrosys.com)
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
#############################################################################
import base64
import io
import xlsxwriter
from odoo import http
from odoo.http import content_disposition, request


class ExcelReportController(http.Controller):
    """This class includes the function to downloads excel report."""
    @http.route(
        [
            '/products_download/excel_report/<model("product.export"):wizards>',
        ],
        type="http",
        auth="public",
        csrf=False,
    )
    def get_product_excel_report(self, wizards=None):
        """
        Downloads the Excel document with the details of products
        """
        response = request.make_response(
            None,
            headers=[
                ("Content-Type", "application/vnd.ms-excel"),
                ("Content-Disposition", content_disposition("Products" + ".xlsx")),
            ],
        )
        # Create workbook object from xlsxwriter library
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        # Create styles to set up the font type, the font size, the border,
        # and the alignment
        header_style = workbook.add_format(
            {
                "text_wrap": True,
                "font_name": "Times",
                "bold": True,
                "left": 1,
                "bottom": 1,
                "right": 1,
                "top": 1,
                "align": "center",
            }
        )
        text_style = workbook.add_format(
            {
                "text_wrap": True,
                "font_name": "Times",
                "left": 1,
                "bottom": 1,
                "right": 1,
                "top": 1,
                "align": "left",
            }
        )
        product_lines = wizards.get_product_lines()
        sheet = workbook.add_worksheet("Products")
        sheet.set_landscape()
        sheet.set_paper(9)
        sheet.merge_range("A1:G1", "PRODUCTS", header_style)
        sheet.set_margins(0.5, 0.5, 0.5, 0.5)
        sheet.set_column("A:A", 5)
        sheet.set_column("B:F", 15)
        sheet.set_column("G:G", 20)
        sheet.set_row(1, 30)
        sheet.set_row(0, 30)
        # Table title
        sheet.write(2, 0, "ID", header_style)
        sheet.write(2, 1, "Internal Reference", header_style)
        sheet.write(2, 2, "Name", header_style)
        sheet.write(2, 3, "Cost", header_style)
        sheet.write(2, 4, "Sales Price", header_style)
        sheet.write(2, 5, "Product Category", header_style)
        sheet.write(2, 6, "Image", header_style)
        row = 3
        number = 1
        count = 0
        for line in product_lines:
            sheet.set_row(row, 128)
            # The report content
            count += 1
            sheet.write(row, 0, count, text_style)
            if line["internal_reference"]:
                sheet.write(row, 1, line["internal_reference"], text_style)
            elif not line["internal_reference"]:
                sheet.write(row, 1, "", text_style)
            sheet.write(row, 2, line["name"], text_style)
            sheet.write(row, 3, str(line["currency"]) + str(line["cost"]), text_style)
            sheet.write(
                row, 4, str(line["currency"]) + str(line["sales_price"]), text_style
            )
            sheet.write(row, 5, line["category"], text_style)
            if line["image"]:
                image_data = io.BytesIO(base64.b64decode(line["image"]))
                sheet.write(row, 6, "", text_style)
                sheet.insert_image(row, 6, "image.png", {"image_data": image_data})
            row += 1
            number += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
        return response
