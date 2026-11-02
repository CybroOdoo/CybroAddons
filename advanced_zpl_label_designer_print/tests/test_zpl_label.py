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
import base64
import io

from PIL import Image

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestZplLabel(TransactionCase):
    """Cover size conversion, ZPL generation, designer saving and printing."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_model = cls.env['ir.model']._get('product.template')
        cls.template = cls.env['zpl.label.template'].create({
            'name': 'Test Label',
            'model_id': cls.product_model.id,
            'width': 101.6,
            'height': 152.4,
            'unit': 'mm',
            'dpi': '203',
        })
        cls.name_field = cls.env['ir.model.fields']._get('product.template', 'name')
        cls.product = cls.env['product.template'].create({'name': 'Label Product'})

    def _create_element(self, **vals):
        values = {'template_id': self.template.id, 'name': 'Element'}
        values.update(vals)
        return self.env['zpl.label.element'].create(values)

    def test_size_in_dots_for_mm_and_inches(self):
        """A 4 inch wide label is 812 dots at 203 DPI in either unit."""
        mm_dots = self.template._get_label_size_in_dots()
        self.assertAlmostEqual(mm_dots[0], 812.0, places=3)
        self.assertAlmostEqual(mm_dots[1], 1218.0, places=3)
        inch_template = self.template.copy({'unit': 'in', 'width': 4.0, 'height': 6.0})
        inch_dots = inch_template._get_label_size_in_dots()
        self.assertAlmostEqual(inch_dots[0], 812.0, places=3)
        self.assertAlmostEqual(inch_dots[1], 1218.0, places=3)

    def test_inch_unit_scales_element_position(self):
        """Element positions scale with the label size in inches."""
        inch_template = self.template.copy({'unit': 'in', 'width': 4.0, 'height': 6.0})
        self.env['zpl.label.element'].create({
            'template_id': inch_template.id,
            'name': 'Box',
            'type': 'rect',
            'x_pos': 500,
            'y_pos': 0,
        })
        self.assertIn('^FO812,0', inch_template.generate_zpl_for_product(None))

    def test_text_uses_field_value_and_data_format(self):
        """Linked fields feed the text; data format wraps it."""
        self._create_element(
            type='text', field_id=self.name_field.id, data_format='Item: {{value}}',
        )
        zpl = self.template.generate_zpl_for_product(self.product)
        self.assertIn('^FDItem: Label Product^FS', zpl)

    def test_rotation_sets_zpl_orientation(self):
        """Rotation is written as the ZPL field orientation."""
        self._create_element(type='text', rotation='90')
        self.assertIn('^A0R,', self.template.generate_zpl_for_product(None))

    def test_image_element_generates_graphic_field(self):
        """Image elements print a real ^GFA graphic, not a placeholder."""
        buffer = io.BytesIO()
        Image.new('RGB', (16, 8), (0, 0, 0)).save(buffer, format='PNG')
        self._create_element(
            type='image', width=16, height=8, x_pos=0, y_pos=0,
            image=base64.b64encode(buffer.getvalue()).decode(),
        )
        scale = self.template._get_label_size_in_dots()[0] / 500.0
        zpl = self.template.generate_zpl_for_product(None)
        self.assertNotIn('[IMAGE', zpl)
        width_dots = int(16 * scale)
        self.assertIn('^GFA,', zpl)
        self.assertIn(f',{(width_dots + 7) // 8},', zpl)

    def test_image_element_without_picture_prints_nothing(self):
        """An image element without a picture adds no command."""
        self._create_element(type='image')
        self.assertNotIn('^GFA', self.template.generate_zpl_for_product(None))

    def test_save_design_updates_in_place(self):
        """Saving updates elements in place and removes deleted ones."""
        kept = self._create_element(
            type='text', rotation='180', data_format='Price: {{value}}', x_pos=5,
        )
        removed = self._create_element(type='text')
        result = self.env['zpl.label.template'].save_design_from_js(
            self.template.id,
            [
                {'db_id': kept.id, 'name': 'Element', 'type': 'text', 'x_pos': 40},
                {'name': 'Brand New', 'type': 'rect', 'x_pos': 1, 'y_pos': 2},
            ],
        )
        self.assertTrue(result)
        self.assertTrue(kept.exists())
        self.assertFalse(removed.exists())
        self.assertEqual(kept.x_pos, 40)
        self.assertEqual(kept.rotation, '180')
        self.assertEqual(kept.data_format, 'Price: {{value}}')
        self.assertEqual(len(self.template.element_ids), 2)
        self.assertTrue(self.template.element_ids.filtered(lambda e: e.name == 'Brand New'))

    def test_render_without_data(self):
        """Previewing a template passes no data and must still render."""
        self._create_element(type='text')
        report = self.env.ref('advanced_zpl_label_designer_print.action_report_zpl_label_instance')
        content, extension = report._render_qweb_text(report.report_name, self.template.ids)
        self.assertEqual(extension, 'txt')
        self.assertTrue(content.startswith(b'^XA'))

    def test_render_for_records_repeats_by_quantity(self):
        """Each record is printed once per requested copy."""
        self._create_element(type='text', field_id=self.name_field.id)
        report = self.env.ref('advanced_zpl_label_designer_print.action_report_zpl_label_instance')
        content, _extension = report._render_qweb_text(
            report.report_name,
            self.template.ids,
            data={'zpl_template_id': self.template.id, 'product_ids': self.product.ids, 'quantity': 3},
        )
        self.assertEqual(content.decode().count('^XA'), 3)

    def test_label_wizard_requires_template(self):
        """The product label wizard asks for a template before printing."""
        wizard = self.env['product.label.layout'].create({
            'product_tmpl_ids': [(6, 0, self.product.ids)],
            'print_format': 'advanced_zpl_label_designer_print',
        })
        with self.assertRaises(UserError):
            wizard.process()

    def test_label_wizard_returns_zpl_report(self):
        """The wizard returns the ZPL report action."""
        wizard = self.env['product.label.layout'].create({
            'product_tmpl_ids': [(6, 0, self.product.ids)],
            'print_format': 'advanced_zpl_label_designer_print',
            'zpl_template_id': self.template.id,
            'custom_quantity': 2,
        })
        action = wizard.process()
        self.assertEqual(action['report_name'], 'advanced_zpl_label_designer_print.report_zpl_view')
        self.assertEqual(action['data']['product_ids'], self.product.ids)
        self.assertEqual(action['data']['quantity'], 2)

    def test_name_based_content_without_linked_field(self):
        """Without a linked field, content is guessed from the name."""
        self.product.write({'default_code': 'REF-1', 'barcode': '123456'})
        for name in ('Product Name', 'Sale Price', 'Barcode', 'Internal Ref', 'Weight', 'Description'):
            self._create_element(type='text', name=name)
        zpl = self.template.generate_zpl_for_product(self.product)
        self.assertIn('^FDLabel Product^FS', zpl)
        self.assertIn('^FDREF-1^FS', zpl)
        self.assertIn('^FD123456^FS', zpl)

    def test_barcode_qrcode_and_shapes(self):
        """Every element type produces its own ZPL command."""
        for barcode_type, command in (
            ('code128', '^BC'), ('code39', '^B3'), ('ean13', '^BE'), ('upca', '^BU'),
        ):
            self._create_element(type='barcode', barcode_type=barcode_type)
            self.assertIn(command, self.template.generate_zpl_for_product(None))
            self.template.element_ids.unlink()
        self._create_element(type='qrcode')
        self._create_element(type='rect', thickness=3, rounding=2)
        self._create_element(type='line')
        zpl = self.template.generate_zpl_for_product(None)
        self.assertIn('^BQN,2,', zpl)
        self.assertEqual(zpl.count('^GB'), 2)

    def test_unreadable_image_prints_nothing(self):
        """A file that is not a picture is ignored."""
        self._create_element(type='image', image=base64.b64encode(b'not a picture').decode())
        self.assertNotIn('^GFA', self.template.generate_zpl_for_product(None))

    def test_preview_action(self):
        """The preview button returns the ZPL report action."""
        action = self.template.action_preview()
        self.assertEqual(action['report_name'], 'advanced_zpl_label_designer_print.report_zpl_view')

    def test_save_design_unknown_template(self):
        """Saving a deleted template reports failure."""
        self.assertFalse(self.env['zpl.label.template'].save_design_from_js(0, []))

    def test_render_missing_template(self):
        """Rendering without a valid template returns an error label."""
        report = self.env.ref('advanced_zpl_label_designer_print.action_report_zpl_label_instance')
        content, _extension = report._render_qweb_text(report.report_name, [0])
        self.assertIn(b'Template Error', content)

    def test_label_wizard_for_product_variants(self):
        """Variant templates print one label set per variant."""
        variant_template = self.template.copy({
            'model_id': self.env['ir.model']._get('product.product').id,
        })
        wizard = self.env['product.label.layout'].create({
            'product_tmpl_ids': [(6, 0, self.product.ids)],
            'print_format': 'advanced_zpl_label_designer_print',
            'zpl_template_id': variant_template.id,
        })
        action = wizard.process()
        self.assertEqual(action['data']['product_ids'], self.product.product_variant_ids.ids)
