# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
"""XLSX writer of the dynamic reports."""
import io
import re

import xlsxwriter
from PIL import Image

PANEL = '#F8F9FA'


def _logo(data):
    """Logo (raw bytes), its scale and (width, height) scaled to 36px high
    (at most 110px wide), or None when it is not a raster image xlsxwriter
    can embed (e.g. SVG)."""
    if not data:
        return None
    raw = bytes(data)
    try:
        with Image.open(io.BytesIO(raw)) as image:
            if image.format not in ('PNG', 'JPEG', 'GIF', 'BMP'):
                return None
            width, height = image.size
    except Exception:  # noqa: BLE001 - an unreadable logo is just left out
        return None
    scale = min(36.0 / height, 110.0 / width)
    return raw, scale, (width * scale, height * scale)


def write_xlsx_table(env, data, response):
    """Write a workbook built from a normalised table into
    ``response.stream``::

        {'title': str, 'columns': [{'label', 'width', 'num'}],
         'rows': [{'cells': [...], 'bold': bool, 'indent': int,
                   'kind': str, 'style': str}],
         'company_name', 'company_address', 'kit_logo' (raw bytes),
         'heading_line', 'filters_line', 'print_stamp', 'num_format'}

    Looks like the PDF (the grid only on screen, not printed): a light
    grey panel with the logo,
    company and address, the title, the period in words with the currency
    and the filters; light lines between rows; ``kind`` ``main`` rows on a
    grey band, a line over ``subtotal`` amounts, line over and double line
    under the ``grand`` total; zero amounts in light grey (still numbers),
    negatives in red. ``style`` ('1' to '6', the financial report line
    style) sets underline, italic and a smaller font; ``indent`` uses the
    cell indent of Excel and the Excel grouping. The header row stays
    visible when scrolling and is repeated on printed pages; the sheet
    prints on the page width (landscape with more than 4 amount columns)
    with the print date and page number in the footer.
    """
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    title = data.get('title') or 'Report'
    # tab named after the report (characters Excel refuses removed)
    sheet = workbook.add_worksheet(re.sub(r'[\[\]:*?/\\]', ' ', title)[:31].strip() or None)
    workbook.set_properties({'title': title, 'company': data.get('company_name') or ''})
    # the spreadsheet grid on screen, not on printed pages
    sheet.hide_gridlines(1)
    # a little more air between the lines than the default 15
    sheet.set_default_row(18)
    columns = data.get('columns', [])
    ncols = max(len(columns), 1)

    # ---------------------------------------------------------------- panel
    # The logo has a row of its own at the top of the panel: a cell indent
    # beside it is drawn with a different width by each spreadsheet program.
    logo = _logo(data.get('kit_logo'))

    def panel_fmt(**props):
        return workbook.add_format({'bg_color': PANEL, 'valign': 'vcenter', **props})
    lines = [('', panel_fmt(), 33)] if logo else []
    lines += [
        (data.get('company_name') or '', panel_fmt(bold=True, font_color='#6C757D'), 18),
        (data.get('company_address') or '', panel_fmt(font_size=9, font_color='#6C757D'), 15),
        (title, panel_fmt(bold=True, font_size=18, font_color='#1F2937'), 30),
        (data.get('heading_line') or '', panel_fmt(font_color='#212529'), 18),
    ]
    if data.get('filters_line'):
        lines.append((data['filters_line'], panel_fmt(font_size=9, font_color='#868E96'), 15))
    for row, (text, fmt, height) in enumerate(lines):
        sheet.set_row(row, height)
        if ncols > 1:
            sheet.merge_range(row, 0, row, ncols - 1, text, fmt)
        else:
            sheet.write(row, 0, text, fmt)
    if logo:
        raw, scale, (__, height) = logo
        sheet.insert_image(0, 0, 'logo.png', {
            'image_data': io.BytesIO(raw), 'x_scale': scale, 'y_scale': scale,
            'x_offset': 6, 'y_offset': max(int((44 - height) / 2), 2),
            'object_position': 3})
    row = len(lines) + 1

    # ---------------------------------------------------------- header row
    header = {
        num: workbook.add_format({
            'bold': True, 'bottom': 2, 'bottom_color': '#868E96',
            'align': 'right' if num else 'left'})
        for num in (True, False)}
    for col_idx, col in enumerate(columns):
        sheet.set_column(col_idx, col_idx, col.get('width', 16))
        sheet.write(row, col_idx, col.get('label', ''), header[bool(col.get('num'))])
    sheet.freeze_panes(row + 1, 0)
    # group buttons beside the heading rows (they are above their lines)
    sheet.outline_settings(True, False, True, False)
    sheet.repeat_rows(row)
    sheet.set_paper(9)  # A4
    sheet.fit_to_pages(1, 0)
    if sum(1 for col in columns if col.get('num')) > 4:
        sheet.set_landscape()
    if data.get('print_stamp'):
        sheet.set_footer('&L&8Printed %s&R&8Page &P / &N'
                         % data['print_stamp'].replace('&', '&&'))
    row += 1

    # ------------------------------------------------------------- lines
    styles = {'1': {'underline': 1}, '3': {'font_size': 10},
              '5': {'italic': True, 'font_size': 10}, '6': {'font_size': 9}}
    num_format = data.get('num_format') or '#,##0.00;[Red]-#,##0.00'
    formats = {}

    def cell_format(is_num, bold, kind, style, indent=0, zero=False):
        key = (is_num, bold, kind, style, indent, zero)
        if key not in formats:
            props = {'bottom': 1, 'bottom_color': '#E3E6E8', 'bold': bool(bold),
                     **styles.get(style or '', {})}
            if kind == 'main':
                props['bg_color'] = '#F3F4F6'
            if is_num:
                props['num_format'] = num_format
                if zero:
                    props['font_color'] = '#ADB5BD'
                if kind == 'subtotal':
                    props.update({'top': 1, 'top_color': '#495057'})
                elif kind == 'grand':
                    props.update({'top': 1, 'top_color': '#212529',
                                  'bottom': 6, 'bottom_color': '#212529'})
            elif kind == 'grand':
                props['bottom'] = 0
            if indent:
                props['indent'] = indent
            formats[key] = workbook.add_format(props)
        return formats[key]

    currency_digits = data.get('currency_digits', 2)
    for line in data.get('rows', []):
        cells = line.get('cells', [])
        bold = line.get('bold')
        kind = line.get('kind') or ''
        style = line.get('style')
        indent = line.get('indent', 0)
        if indent:
            # Excel grouping (1 / 2 / 3 buttons) from the report hierarchy
            sheet.set_row(row, None, None, {'level': min(indent, 7)})
        for col_idx, col in enumerate(columns):
            val = cells[col_idx] if col_idx < len(cells) else ''
            if isinstance(val, dict):
                # A translated (jsonb) field selected via raw SQL comes
                # back as ``{lang: value}``; pick the active language.
                lang = env.context.get('lang') or 'en_US'
                val = val.get(lang) or next(iter(val.values()), '')
            if col.get('num') and isinstance(val, (int, float)) \
                    and not isinstance(val, bool):
                zero = round(val, currency_digits) == 0
                sheet.write(row, col_idx, 0.0 if zero else val,
                            cell_format(True, bold, kind, style, zero=zero))
            else:
                sheet.write(row, col_idx, val if val is not None else '',
                            cell_format(False, bold, kind, style,
                                        indent if col_idx == 0 else 0))
        row += 1

    workbook.close()
    output.seek(0)
    response.stream.write(output.read())
    output.close()
