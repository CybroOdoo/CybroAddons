# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class ZplLabelTemplate(models.Model):
    _name = 'zpl.label.template'
    _description = 'ZPL Label Template'

    name = fields.Char(
        string='Template Name', required=True,
        help="Name used to identify this ZPL template, shown in the "
             "'Choose Labels Layout' wizard when printing labels.")
    model_id = fields.Many2one(
        'ir.model', required=True, ondelete='cascade',
        help="Odoo model this template is designed for (e.g. Product "
             "Variant or Product Template). Determines which records and "
             "fields can be used to fill this template's elements.")
    width = fields.Float(
        default=101.6,
        help="Label width, in the unit selected below.")
    height = fields.Float(
        default=152.4,
        help="Label height, in the unit selected below.")
    unit = fields.Selection(
        [('mm', 'mm'), ('in', 'inches')], default='mm',
        required=True, help="Unit used for the Width and Height fields.")
    dpi = fields.Selection(
        [('203', '203 DPI'), ('300', '300 DPI'), ('600', '600 DPI')],
        default='203', required=True,
        help="Printer resolution used to convert the design canvas "
             "coordinates into ZPL dots.")

    element_ids = fields.One2many(
        'zpl.label.element', 'template_id', string='Elements',
        help="Text, barcode, QR code and shape elements that make up this "
             "label design.")
    zpl_content = fields.Text(
        string='Sample ZPL Code', compute='_compute_zpl_content', store=True,
        help="Generated ZPL code preview for this template, without data "
             "from an actual record.")

    @api.depends('element_ids', 'width', 'height', 'dpi')
    def _compute_zpl_content(self):
        """Recompute the sample ZPL preview whenever the template's
        elements, dimensions or DPI change, by generating ZPL with no
        bound record."""
        for rec in self:
            rec.zpl_content = rec.generate_zpl_for_product(None)

    def action_preview(self):
        """Return the report action that previews this template's ZPL
        output, as if printed for a single record."""
        self.ensure_one()

        action = self.env.ref(
            'advanced_zpl_label_designer_print.action_report_zpl_label_instance'
        ).report_action(self)

        return action

    def generate_zpl_for_product(self, record=None):
        """Render this template's elements into a ZPL string.
        If ``record`` is given, each element's configured Odoo field (or
        legacy name-based fallback) is used to fill in its content;
        otherwise elements are rendered using their static name/label.
        """
        zpl = ["^XA"]

        # Calculate scaling from 500x600 canvas to dots
        dots_w = (self.width / 25.4) * float(self.dpi)
        dots_h = (self.height / 25.4) * float(self.dpi)

        scale_x = dots_w / 500.0
        scale_y = dots_h / 600.0

        for el in self.element_ids:
            # Important: Use calculated scale to convert canvas pixels to dots
            x = int(el.x_pos * scale_x)
            y = int(el.y_pos * scale_y)
            w = int(el.width * scale_x) if el.width else 0
            h = int(el.height * scale_y) if el.height else 0

            content = el.name
            if record:
                if el.field_id:
                    # Use the configured Odoo field if available
                    field_name = el.field_id.name
                    if field_name in record._fields:
                        field_value = record[field_name]
                        if hasattr(field_value, 'display_name'):
                            content = field_value.display_name or ""
                        else:
                            content = str(field_value) if field_value is not False else ""
                    else:
                        content = ""
                else:
                    # Fallback to name-based logic (legacy)
                    name_lower = el.name.lower()
                    if "name" in name_lower:
                        content = getattr(record, 'display_name', getattr(record, 'name', ""))
                    elif "price" in name_lower and hasattr(record, 'lst_price'):
                        content = f"{record.lst_price:.2f}"
                    elif "barcode" in name_lower:
                        content = getattr(record, 'barcode', "") or ""
                    elif "sku" in name_lower or "ref" in name_lower or "internal" in name_lower:
                        content = getattr(record, 'default_code', "") or ""
                    elif "weight" in name_lower:
                        content = f"{getattr(record, 'weight', 0):.2f}"
                    elif "description" in name_lower:
                        content = getattr(record, 'description_sale', getattr(record, 'name', "")) or ""

                if el.data_format:
                    # Basic template replacement if data_format is used
                    content = el.data_format.replace("{{value}}", content)

            if el.type == 'text':
                # ^A0N,height,width
                h = el.font_size or 30
                zpl.append(f"^FO{x},{y}^A0N,{h},{h}^FD{content}^FS")
            elif el.type == 'barcode':
                # Barcode Type mapping
                b_type = el.barcode_type or 'code128'
                h = el.font_size or 100

                cmd = "^BC"
                if b_type == 'code39':
                    cmd = "^B3"
                elif b_type == 'ean13':
                    cmd = "^BE"
                elif b_type == 'upca':
                    cmd = "^BU"

                zpl.append(f"^FO{x},{y}^BY2{cmd}N,{h},Y,N,N^FD{content}^FS")
            elif el.type == 'qrcode':

                mag = min(max(int((el.width or 100) / 40), 1), 10)
                zpl.append(f"^FO{x},{y}^BQN,2,{mag}^FDQA,{content}^FS")
            elif el.type == 'rect':
                t = el.thickness or 2
                r = el.rounding or 0
                zpl.append(f"^FO{x},{y}^GB{w},{h},{t},B,{r}^FS")
            elif el.type == 'line':
                t = el.thickness or 2
                zpl.append(f"^FO{x},{y}^GB{w or 1},{h or 1},{t},B,0^FS")
            elif el.type == 'image':
                zpl.append(f"^FO{x},{y}^FD[IMAGE: {el.name}]^FS")

        zpl.append("^XZ")
        return "\n".join(zpl)

    @api.model
    def save_design_from_js(self, template_id, elements):
        """Replace the elements of the given template with those sent by
        the JS label designer.
        :param template_id: id of the ``zpl.label.template`` to update.
        :param elements: list of dicts describing each element to create
            (name, position, size, type, field_id, etc).
        :return: True if the template was found and updated, False otherwise.
        """
        template = self.browse(template_id)

        if template.exists():
            template.element_ids.unlink()

            for el in elements:
                self.env['zpl.label.element'].create({
                    'template_id': template.id,
                    'name': el.get('name', 'New Element'),
                    'x_pos': el.get('x_pos', 0),
                    'y_pos': el.get('y_pos', 0),
                    'width': el.get('width', 100),
                    'height': el.get('height', 50),
                    'thickness': el.get('thickness', 2),
                    'rounding': el.get('rounding', 0),
                    'font_size': el.get('font_size', 20),
                    'barcode_type': el.get('barcode_type', 'code128'),
                    'type': el.get('type', 'text'),
                    'field_id': el.get('field_id'),
                })

            template._compute_zpl_content()

            return True

        return False
