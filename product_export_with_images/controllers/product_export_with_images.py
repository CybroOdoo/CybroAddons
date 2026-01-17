# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################
import base64
import io
import xlsxwriter
from io import BytesIO
from odoo import http
from odoo.http import content_disposition, request
from odoo.tools.image import image_process
from PIL import Image
import traceback


class ExcelReportController(http.Controller):
    """Controller to download Excel report of selected products with images."""

    @http.route(
        ['/products_download/excel_report/<model("product.export"):wizards>'],
        type="http",
        auth="public",
        csrf=False,
    )
    def get_product_excel_report(self, wizards=None):
        """Download an Excel file containing details of selected products."""
        response = request.make_response(
            None,
            headers=[
                ("Content-Type", "application/vnd.ms-excel"),
                ("Content-Disposition", content_disposition("Products.xlsx")),
            ],
        )

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})

        # Define formats
        header_style = workbook.add_format({
            "text_wrap": True, "font_name": "Times", "bold": True,
            "left": 1, "bottom": 1, "right": 1, "top": 1, "align": "center"
        })
        text_style = workbook.add_format({
            "text_wrap": True, "font_name": "Times",
            "left": 1, "bottom": 1, "right": 1, "top": 1, "align": "left"
        })

        # Get all selected products
        product_lines = wizards.get_product_lines()

        # Create sheet
        sheet = workbook.add_worksheet("Products")
        sheet.set_landscape()
        sheet.set_paper(9)
        sheet.merge_range("A1:G1", "PRODUCTS", header_style)
        sheet.set_margins(0.5, 0.5, 0.5, 0.5)
        sheet.set_column("A:A", 5)
        sheet.set_column("B:F", 15)
        sheet.set_column("G:G", 20)
        sheet.set_row(0, 30)
        sheet.set_row(1, 30)

        # Table header
        headers = ["ID", "Internal Reference", "Name", "Cost", "Sales Price", "Product Category", "Image"]
        for col, val in enumerate(headers):
            sheet.write(2, col, val, header_style)

        row = 3
        for count, line in enumerate(product_lines, start=1):
            sheet.set_row(row, 128)  # Row height for images
            sheet.write(row, 0, count, text_style)
            sheet.write(row, 1, line.get("internal_reference", ""), text_style)
            sheet.write(row, 2, line.get("name", ""), text_style)
            sheet.write(row, 3, f'{line.get("currency", "")}{line.get("cost", "")}', text_style)
            sheet.write(row, 4, f'{line.get("currency", "")}{line.get("sales_price", "")}', text_style)
            sheet.write(row, 5, line.get("category", ""), text_style)
            sheet.write(row, 6, "", text_style)


            # Handle images

            if line.get("image"):
                try:
                    image_data_raw = base64.b64decode(line["image"])
                    image_obj = Image.open(io.BytesIO(image_data_raw))
                    image_type = image_obj.format.lower()

                    if image_type in ["jpeg", "png", "gif", "bmp"]:
                        processed_image = image_process(image_data_raw, size=(300, 300))
                        sheet.insert_image(row, 6, f"product.{image_type}", {"image_data": BytesIO(processed_image)})

                    elif image_type == "webp":
                        # Convert WebP to PNG
                        with BytesIO() as png_output:
                            image_obj.save(png_output, format="PNG")
                            processed_image = image_process(png_output.getvalue(), size=(300, 300))
                            sheet.insert_image(row, 6, "product.png", {"image_data": BytesIO(processed_image)})

                except Exception:
                    traceback.print_exc()

            row += 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
        return response
