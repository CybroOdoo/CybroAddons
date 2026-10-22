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
#############################################################################
import base64
import logging
from io import BytesIO
import xlsxwriter
from werkzeug.exceptions import Forbidden, NotFound

from odoo import http
from odoo.http import request
from odoo.http.stream import content_disposition
from odoo.tools.image import image_process
from PIL import Image

_logger = logging.getLogger(__name__)


def _get_image_bytes(image_data):
    """ Extract raw binary bytes from image field value.
    Handles Odoo BinaryValue / BinaryValueAttachment objects,
    base64 strings, base64 bytes, and raw binary bytes. """
    if not image_data:
        return None
    if hasattr(image_data, 'content') and image_data.content:
        return image_data.content
    if hasattr(image_data, 'to_base64'):
        try:
            b64_str = image_data.to_base64()
            if b64_str:
                return base64.b64decode(b64_str)
        except Exception as err:
            _logger.debug("Failed to convert image to base64 bytes: %s", err)
    if isinstance(image_data, str):
        try:
            return base64.b64decode(image_data)
        except Exception as err:
            _logger.debug("Failed to decode string image data: %s", err)
            return None
    if isinstance(image_data, bytes):
        try:
            return base64.b64decode(image_data)
        except Exception as err:
            _logger.debug("Image data already raw bytes or decode failed: %s", err)
            return image_data
    return None


class ExcelReportController(http.Controller):
    """Controller to download Excel report of selected products with images."""

    @http.route(
        ['/products_download/excel_report/<model("product.export"):wizards>'],
        type="http",
        auth="user",
    )
    def get_product_excel_report(self, wizards=None):
        """Download an Excel file containing details of selected products."""
        if not wizards or not wizards.exists():
            raise NotFound()
        if not request.env.user.has_group(
            "product_export_with_images.group_product_export_with_images"
        ):
            raise Forbidden()
        if wizards.create_uid != request.env.user and not request.env.is_admin():
            raise Forbidden()

        response = request.make_response(
            None,
            headers=[
                (
                    "Content-Type",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ),
                ("Content-Disposition", content_disposition("Products.xlsx")),
            ],
        )

        output = BytesIO()
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
            sheet.write(row, 1, line.get("internal_reference", "") or "", text_style)
            sheet.write(row, 2, line.get("name", "") or "", text_style)
            sheet.write(row, 3, f'{line.get("currency", "")}{line.get("cost", "")}', text_style)
            sheet.write(row, 4, f'{line.get("currency", "")}{line.get("sales_price", "")}', text_style)
            sheet.write(row, 5, line.get("category", "") or "", text_style)
            sheet.write(row, 6, "", text_style)

            # Handle images
            image_val = line.get("image")
            image_data_raw = _get_image_bytes(image_val)

            if image_data_raw:
                try:
                    image_obj = Image.open(BytesIO(image_data_raw))
                    image_type = image_obj.format.lower() if image_obj.format else "png"

                    if image_type == "webp":
                        # Convert WebP to PNG
                        with BytesIO() as png_output:
                            image_obj.save(png_output, format="PNG")
                            image_data_raw = png_output.getvalue()
                            image_type = "png"

                    if image_type in ["jpeg", "jpg", "png", "gif", "bmp"]:
                        processed_image = image_process(image_data_raw, size=(120, 120))
                        final_bytes = processed_image if isinstance(processed_image, bytes) and processed_image else image_data_raw
                        sheet.insert_image(
                            row, 6, f"product.{image_type}",
                            {
                                "image_data": BytesIO(final_bytes),
                                "x_offset": 10,
                                "y_offset": 10,
                                "positioning": 1,
                            }
                        )
                except Exception as err:
                    _logger.warning("Could not process product image for row %s: %s", row, err)

            row += 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
        return response
