# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Harshitha AP (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) asx`
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
import base64
import io
from odoo.addons.web.controllers.export import ExportXlsxWriter

IMAGE_MAX_PX     = 90
IMAGE_ROW_HEIGHT = 70
IMAGE_COL_WIDTH  = 14


def _is_image_field(field_name: str) -> bool:
    name = str(field_name).lower().split('/')[-1]
    return name == 'image' or name.startswith('image_')


def _to_png_stream(raw: bytes):
    from PIL import Image as PILImage
    with PILImage.open(io.BytesIO(raw)) as im:
        w, h = im.size
        mode = 'RGBA' if im.mode in ('RGBA', 'LA', 'P') else 'RGB'
        im = im.convert(mode)
        out = io.BytesIO()
        im.save(out, format='PNG')
        out.seek(0)
    s = min(IMAGE_MAX_PX / w, IMAGE_MAX_PX / h, 1.0) if (w and h) else 0.3
    return out, s, s


def _patch_base_export():
    from odoo.fields import Binary
    _orig_convert = Binary.convert_to_export

    def _new_convert(self, value, record):
        if _is_image_field(self.name) and value:
            if isinstance(value, bytes):
                return value
            return base64.b64decode(value)
        return _orig_convert(self, value, record)

    Binary.convert_to_export = _new_convert


def _patch_xlsx_writer():
    _orig_init       = ExportXlsxWriter.__init__
    _orig_write_cell = ExportXlsxWriter.write_cell

    def _new_init(self, field_names, columns_headers, row_count, **kwargs):
        _orig_init(self, field_names, columns_headers, row_count, **kwargs)
        self._img_field_names     = [
            (f.get('name', '') if isinstance(f, dict) else str(f))
            for f in field_names
        ]
        self._img_row_heights_set = set()
        self._img_col_widths_set  = set()

    def _new_write_cell(self, row, col, cell_value):
        try:
            field_name = self._img_field_names[col]
        except (AttributeError, IndexError):
            field_name = ''

        if not (field_name and _is_image_field(field_name) and cell_value):
            return _orig_write_cell(self, row, col, cell_value)

        try:
            s = cell_value.strip() if isinstance(cell_value, str) else cell_value
            if isinstance(s, str) and s.startswith('data:') and ',' in s:
                s = s.split(',', 1)[1]
            raw = base64.b64decode(s)
            stream, xs, ys = _to_png_stream(raw)
            self.worksheet.insert_image(
                row, col, 'img.png',
                {
                    'image_data'     : stream,
                    'x_scale'        : xs,
                    'y_scale'        : ys,
                    'x_offset'       : 2,
                    'y_offset'       : 2,
                    'object_position': 1,
                }
            )
            if row not in self._img_row_heights_set:
                self.worksheet.set_row(row, IMAGE_ROW_HEIGHT)
                self._img_row_heights_set.add(row)
            if col not in self._img_col_widths_set:
                self.worksheet.set_column(col, col, IMAGE_COL_WIDTH)
                self._img_col_widths_set.add(col)
        except Exception:
            _orig_write_cell(self, row, col, '')

    ExportXlsxWriter.__init__   = _new_init
    ExportXlsxWriter.write_cell = _new_write_cell


_patch_base_export()
_patch_xlsx_writer()
