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
import io
import logging

from PIL import Image as PILImage

from odoo.addons.web.controllers.export import (
    ExcelExport,
    ExportXlsxWriter,
    GroupExportXlsxWriter,
)
from odoo.http import request, route

_logger = logging.getLogger(__name__)

IMAGE_MAX_PX = 90
IMAGE_ROW_HEIGHT = 70
IMAGE_COL_WIDTH = 14
IMAGE_NAME_KEYWORDS = (
    'image', 'avatar', 'photo', 'signature', 'logo', 'icon', 'picture', 'thumbnail',
)


def _is_candidate_image_field(field_name: str, field_type: str = '') -> bool:
    """Determine whether a field is likely to contain image data based on type or name.

    :param str field_name: Field name or relational path (e.g. 'image_1920', 'avatar_128', 'partner_id/photo').
    :param str field_type: Field type descriptor if available (e.g. 'binary', 'image').
    :return: True if the field is a candidate image field, False otherwise.
    :rtype: bool
    """
    if field_type in ('image', 'binary'):
        return True
    if not field_name:
        return False
    leaf_name = str(field_name).lower().split('/')[-1]
    return any(keyword in leaf_name for keyword in IMAGE_NAME_KEYWORDS)


def _is_valid_image(raw: bytes) -> bool:
    """Validate whether raw bytes represent a supported image format.

    Uses magic byte signatures for performance followed by PIL verification.

    :param bytes raw: Binary data to test.
    :return: True if raw bytes are a valid supported image, False otherwise.
    :rtype: bool
    """
    if not raw or len(raw) < 8:
        return False
    if not (
        raw.startswith((b'\x89PNG', b'\xff\xd8', b'GIF8', b'BM'))
        or (raw.startswith(b'RIFF') and b'WEBP' in raw[:16])
    ):
        return False
    try:
        with PILImage.open(io.BytesIO(raw)) as im:
            im.verify()
        return True
    except (OSError, ValueError):
        return False


def _decode_image_data(cell_value):
    """Decode raw or base64-encoded image data from a cell value.

    Handles Odoo BinaryValue / BinaryBytes, raw image byte signatures,
    base64-encoded bytes or strings (including data URI schemes), and applies
    missing base64 padding when needed.

    :param cell_value: Cell value containing image data in raw bytes, base64 string, or binary object.
    :return: Decoded raw image bytes if successful, None otherwise.
    :rtype: bytes or None
    """
    if not cell_value:
        return None

    if hasattr(cell_value, 'to_base64'):
        try:
            cell_value = cell_value.to_base64()
        except (AttributeError, TypeError, ValueError):
            cell_value = str(cell_value)

    if isinstance(cell_value, bytes):
        if cell_value.startswith((b'\x89PNG', b'\xff\xd8', b'GIF8', b'BM')) or (
            cell_value.startswith(b'RIFF') and b'WEBP' in cell_value[:16]
        ):
            return cell_value
        stripped = cell_value.strip()
        missing_padding = len(stripped) % 4
        if missing_padding:
            stripped += b'=' * (4 - missing_padding)
        try:
            return base64.b64decode(stripped)
        except (ValueError, TypeError):
            return None

    if isinstance(cell_value, str):
        stripped_str = cell_value.strip()
        if stripped_str.startswith('data:') and ',' in stripped_str:
            stripped_str = stripped_str.split(',', 1)[1]
        cleaned = ''.join(stripped_str.split())
        missing_padding = len(cleaned) % 4
        if missing_padding:
            cleaned += '=' * (4 - missing_padding)
        try:
            return base64.b64decode(cleaned)
        except (ValueError, TypeError):
            return None

    return None


def _to_png_stream(raw: bytes):
    """Convert raw image bytes into a PNG byte stream and calculate scale factors.

    Opens the image with PIL, converts palette/transparency or other formats to
    RGBA or RGB, saves it into an in-memory BytesIO stream as PNG, and computes
    scaling factors to fit within defined maximum dimensions.

    :param bytes raw: Raw binary data of the image.
    :return: Tuple of (out_stream, x_scale, y_scale) containing the PNG stream and scales.
    :rtype: tuple[io.BytesIO, float, float]
    """
    with PILImage.open(io.BytesIO(raw)) as im:
        w, h = im.size
        mode = 'RGBA' if im.mode in ('RGBA', 'LA', 'P') else 'RGB'
        im = im.convert(mode)
        out = io.BytesIO()
        im.save(out, format='PNG')
        out.seek(0)
    scale = min(IMAGE_MAX_PX / w, IMAGE_MAX_PX / h, 1.0) if (w and h) else 0.3
    return out, scale, scale


class ImageExportXlsxWriter(ExportXlsxWriter):
    """ExportXlsxWriter subclass that embeds image thumbnails into Excel cells."""

    def __init__(self, fields, columns_headers, row_count):
        """Initialize the writer and precompute candidate image column indices.

        :param list fields: List of field descriptors or names being exported.
        :param list columns_headers: List of column header titles.
        :param int row_count: Total count of rows to be exported.
        """
        super().__init__(fields, columns_headers, row_count)
        self._image_cols = set()
        for idx, f in enumerate(fields):
            fname = f.get('name', '') if isinstance(f, dict) else str(getattr(f, 'name', f or ''))
            ftype = f.get('type', '') if isinstance(f, dict) else ''
            if _is_candidate_image_field(fname, ftype):
                self._image_cols.add(idx)
        self._img_row_heights_set = set()
        self._img_col_widths_set = set()

    def write_cell(self, row, column, cell_value):
        """Write cell data, embedding images when the column contains valid image data.

        :param int row: Zero-based row index in the worksheet.
        :param int column: Zero-based column index in the worksheet.
        :param cell_value: Content to be written to the cell.
        """
        if column in self._image_cols and cell_value:
            raw = _decode_image_data(cell_value)
            if raw and _is_valid_image(raw):
                try:
                    stream, xs, ys = _to_png_stream(raw)
                    self.worksheet.insert_image(
                        row, column, 'image.png',
                        {
                            'image_data': stream,
                            'x_scale': xs,
                            'y_scale': ys,
                            'x_offset': 2,
                            'y_offset': 2,
                            'object_position': 1,
                        }
                    )
                    if row not in self._img_row_heights_set:
                        self.worksheet.set_row(row, IMAGE_ROW_HEIGHT)
                        self._img_row_heights_set.add(row)
                    if column not in self._img_col_widths_set:
                        self.worksheet.set_column(column, column, IMAGE_COL_WIDTH)
                        self._img_col_widths_set.add(column)
                    return
                except Exception as exc:
                    _logger.warning("Failed to embed image at row %s col %s: %s", row, column, exc)

        super().write_cell(row, column, cell_value)


class ImageGroupExportXlsxWriter(GroupExportXlsxWriter, ImageExportXlsxWriter):
    """Grouped ExportXlsxWriter subclass that embeds image thumbnails into Excel cells."""
    pass


class ExcelExportImage(ExcelExport):
    """Controller extension overriding Excel export to embed image thumbnails."""

    @route()
    def web_export_xlsx(self, data):
        """Handle XLSX export request with support for embedded image rendering."""
        return super().web_export_xlsx(data)

    def _is_image_export_active(self):
        """Check whether 'images_in_excel_file' is installed in the active environment.

        Uses the stable-cached ir.module.module._installed() dictionary, executing
        at most once per request without per-cell database overhead.

        :return: True if images_in_excel_file is active, False otherwise.
        :rtype: bool
        """
        if request and getattr(request, 'env', None):
            try:
                installed = request.env['ir.module.module']._installed()
                return 'images_in_excel_file' in installed
            except Exception:
                return True
        return False

    def from_data(self, fields, columns_headers, rows):
        """Build an XLSX workbook from tabular rows, embedding images when active."""
        if not self._is_image_export_active():
            return super().from_data(fields, columns_headers, rows)

        with ImageExportXlsxWriter(fields, columns_headers, len(rows)) as xlsx_writer:
            for row_index, row in enumerate(rows):
                for cell_index, cell_value in enumerate(row):
                    xlsx_writer.write_cell(row_index + 1, cell_index, cell_value)

        return xlsx_writer.value

    def from_group_data(self, fields, columns_headers, groups):
        """Build an XLSX workbook from grouped records, embedding images when active."""
        if not self._is_image_export_active():
            return super().from_group_data(fields, columns_headers, groups)

        with ImageGroupExportXlsxWriter(fields, columns_headers, groups.count) as xlsx_writer:
            x, y = 1, 0
            for group_name, group in groups.children.items():
                x, y = xlsx_writer.write_group(x, y, group_name, group)

        return xlsx_writer.value
