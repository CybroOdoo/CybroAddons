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
from odoo import api,fields,models


class ZplLabelTemplate(models.Model):
    """A reusable ZPL label design bound to a specific Odoo model,
    made up of positioned elements that can pull data from that model's
    fields when a label is generated for a real record."""
    _name = 'zpl.label.template'
    _description = 'ZPL Label Template'

    name = fields.Char(string='Template Name', required=True)
    model_id = fields.Many2one('ir.model', string='Model', required=True, ondelete='cascade')
    width = fields.Float(string='Width', default=101.6)
    height = fields.Float(string='Height', default=152.4)
    unit = fields.Selection([('mm', 'mm'), ('in', 'inches')], string='Unit', default='mm', required=True)
    dpi = fields.Selection([('203', '203 DPI'), ('300', '300 DPI'), ('600', '600 DPI')], default='203', required=True)

    element_ids = fields.One2many('zpl.label.element', 'template_id', string='Elements')
    zpl_content = fields.Text(string='Sample ZPL Code', compute='_compute_zpl_content', store=True)

    @api.depends('element_ids', 'width', 'height', 'dpi')
    def _compute_zpl_content(self):
        """Refresh the static sample ZPL code shown on the template form,
        rendered without a bound record so elements fall back to their
        literal names."""
        for rec in self:
            rec.zpl_content = rec.generate_zpl_for_product(None)

    def action_preview(self):
        """Open the ZPL report action to preview this template's sample
        ZPL code."""
        self.ensure_one()

        action = self.env.ref(
            'advanced_zpl_label_designer_print.action_report_zpl_label_instance'
        ).report_action(self)

        return action

    def generate_zpl_for_product(self, record=None):
        """Render this template's elements as ZPL code.

        When ``record`` is given, each element's content is pulled from
        the record's configured field (or a legacy name-based guess);
        otherwise the element's own name is used as placeholder text.
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
        """Replace a template's elements with the list built by the
        front-end drag-and-drop designer widget.

        :param int template_id: id of the ``zpl.label.template`` to update
        :param list elements: element dicts as produced by the JS widget
        :return: True if the template was found and updated, False otherwise
        """
        template = self.browse(template_id)

        if template.exists():
            template.element_ids.unlink()

            for el in elements:
                created = self.env['zpl.label.element'].create({
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
