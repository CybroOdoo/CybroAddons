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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
from odoo import api, fields, models

ZPL_ORIENTATION = {'0': 'N', '90': 'R', '180': 'I', '270': 'B'}
JS_ELEMENT_FIELDS = (
    'name', 'type', 'x_pos', 'y_pos', 'width', 'height', 'thickness',
    'rounding', 'font_size', 'barcode_type', 'field_id',
)


class ZplLabelTemplate(models.Model):
    """Store ZPL label templates and generate printer command output."""
    _name = 'zpl.label.template'
    _description = 'ZPL Label Template'

    name = fields.Char(string='Template Name', required=True)
    model_id = fields.Many2one('ir.model', required=True, ondelete='cascade')
    width = fields.Float(default=101.6)
    height = fields.Float(default=152.4)
    unit = fields.Selection([('mm', 'mm'), ('in', 'inches')], default='mm', required=True)
    dpi = fields.Selection([('203', '203 DPI'), ('300', '300 DPI'), ('600', '600 DPI')], default='203', required=True)

    element_ids = fields.One2many('zpl.label.element', 'template_id', string='Elements')
    zpl_content = fields.Text(string='Sample ZPL Code', compute='_compute_zpl_content', store=True)

    @api.depends(
        'width', 'height', 'unit', 'dpi', 'element_ids',
        'element_ids.name', 'element_ids.type', 'element_ids.x_pos',
        'element_ids.y_pos', 'element_ids.width', 'element_ids.height',
        'element_ids.thickness', 'element_ids.rounding', 'element_ids.font_size',
        'element_ids.rotation', 'element_ids.field_id', 'element_ids.data_format',
        'element_ids.barcode_type', 'element_ids.image',
    )
    def _compute_zpl_content(self):
        """Compute sample ZPL content from the template elements."""
        for rec in self:
            rec.zpl_content = rec.generate_zpl_for_product(None)

    def action_preview(self):
        """Open the report preview for the current ZPL template."""
        self.ensure_one()
        action = self.env.ref(
            'advanced_zpl_label_designer_print.action_report_zpl_label_instance'
        ).report_action(self, config=False)
        return action

    def _get_label_size_in_dots(self):
        """Return the label width and height in printer dots."""
        self.ensure_one()
        to_inches = 1.0 if self.unit == 'in' else 1.0 / 25.4
        dpi = float(self.dpi)
        return round(self.width * to_inches * dpi), round(self.height * to_inches * dpi)

    def generate_zpl_for_product(self, record=None):
        """Generate ZPL command text for a template and optional record."""
        self.ensure_one()
        zpl = ["^XA", "^CI28"]

        dots_w, dots_h = self._get_label_size_in_dots()

        scale_x = dots_w / 500.0
        scale_y = dots_h / 600.0

        for el in self.element_ids:
            x = int(el.x_pos * scale_x)
            y = int(el.y_pos * scale_y)
            w = int(el.width * scale_x) if el.width else 0
            h = int(el.height * scale_y) if el.height else 0
            orientation = ZPL_ORIENTATION.get(el.rotation or '0', 'N')

            content = el.name
            if record:
                if el.field_id:
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
                    name_lower = el.name.lower()
                    if "name" in name_lower:
                        content = getattr(record, 'name', getattr(record, 'display_name', ""))

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
                    content = el.data_format.replace("{{value}}", content)

            if el.type == 'text':
                h = el.font_size or 30
                zpl.append(f"^FO{x},{y}^A0{orientation},{h},{h}^FD{content}^FS")
            elif el.type == 'barcode':
                b_type = el.barcode_type or 'code128'
                h = el.font_size or 100

                cmd = "^BC"
                if b_type == 'code39':
                    cmd = "^B3"
                elif b_type == 'ean13':
                    cmd = "^BE"
                elif b_type == 'upca':
                    cmd = "^BU"

                zpl.append(f"^FO{x},{y}^BY2{cmd}{orientation},{h},Y,N,N^FD{content}^FS")
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
                graphic = el._get_zpl_image_command(w, h)
                if graphic:
                    zpl.append(f"^FO{x},{y}{graphic}^FS")
        zpl.append("^XZ")
        return "\n".join(zpl)

    @api.model
    def save_design_from_js(self, template_id, elements):
        """Persist label element positions and settings from the JS designer.

        Elements sent with a ``db_id`` are updated in place, so values the
        designer does not edit (data format, rotation, image) are kept. New
        elements are created and elements removed from the canvas are deleted.
        """
        template = self.browse(template_id)
        if not template.exists():
            return False
        existing = {element.id: element for element in template.element_ids}
        kept = self.env['zpl.label.element']
        for el in elements:
            vals = {key: el[key] for key in JS_ELEMENT_FIELDS if key in el}
            record = existing.get(el.get('db_id'))
            if record:
                record.write(vals)
            else:
                vals.setdefault('name', 'New Element')
                vals['template_id'] = template.id
                record = self.env['zpl.label.element'].create(vals)
            kept |= record
        (template.element_ids - kept).unlink()
        template._compute_zpl_content()
        return True
