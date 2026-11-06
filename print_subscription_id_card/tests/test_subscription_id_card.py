# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies(odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
import io
from unittest.mock import patch

from PIL import Image, WebPImagePlugin  # noqa: F401 - registers the WebP encoder

from odoo.tests import TransactionCase, new_test_user, tagged
from odoo.tools import BinaryBytes

REPORT = 'report.print_subscription_id_card.report_subscription_id_card'


def _image_bytes(fmt, size=(300, 200)):
    buf = io.BytesIO()
    Image.new('RGB', size, (52, 152, 219)).save(buf, fmt)
    return buf.getvalue()


@tagged('post_install', '-at_install')
class TestSubscriptionIdCard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Anna Carter', 'image_1920': BinaryBytes(_image_bytes('PNG')),
        })
        cls.plan = cls.env['sale.subscription.plan'].create({
            'name': 'Monthly', 'billing_period_value': 1, 'billing_period_unit': 'month',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Gym Membership', 'type': 'service', 'recurring_invoice': True,
        })
        cls.order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'plan_id': cls.plan.id,
            'order_line': [
                (0, 0, {'display_type': 'line_section', 'name': 'Memberships'}),
                (0, 0, {'product_id': cls.product.id, 'product_uom_qty': 1}),
            ],
        })
        cls.order.action_confirm()
        cls.Report = cls.env[REPORT]

    def _data(self, order=None):
        action = (order or self.order).action_subscription_id_card()
        self.assertTrue(action['close_on_report_download'])
        context = action.get('context') or {}
        return context['report_action']['data'] if 'report_action' in context else action['data']

    def test_button_data(self):
        data = self._data()
        self.assertEqual(data['name'], 'Anna Carter')
        self.assertEqual(data['partner_id'], self.partner.id)
        self.assertEqual(data['start_date'], self.order.date_order.date())
        # The section line has no product and is left out.
        self.assertEqual(data['products'], ['Gym Membership'])

    def test_button_needs_one_order(self):
        with self.assertRaises(ValueError):
            (self.order | self.order.copy()).action_subscription_id_card()

    def test_png_photo_embedded(self):
        values = self.Report._get_report_values(None, data=self._data())
        self.assertEqual(values['partner'], self.partner)
        self.assertTrue(values['partner_image'].startswith('data:image/png;base64,'))

    def test_webp_photo_converted_to_square_png(self):
        png = self.Report._image_to_png(_image_bytes('WEBP', size=(600, 400)))
        image = Image.open(io.BytesIO(png))
        self.assertEqual((image.format, image.size), ('PNG', (256, 256)))

    def test_photo_without_rgb_mode_converted(self):
        buf = io.BytesIO()
        Image.new('CMYK', (40, 40)).save(buf, 'JPEG')
        self.assertEqual(Image.open(io.BytesIO(self.Report._image_to_png(buf.getvalue()))).format, 'PNG')

    def test_no_photo_uses_avatar(self):
        self.partner.image_1920 = False
        self.assertTrue(self.Report._get_partner_image(self.partner).startswith('data:image/svg+xml'))

    def test_unreadable_photo_falls_back_to_avatar(self):
        with patch.object(type(self.Report), '_image_to_png', side_effect=OSError('broken')), \
                self.assertLogs('odoo.addons.print_subscription_id_card', level='WARNING'):
            uri = self.Report._get_partner_image(self.partner)
        self.assertTrue(uri.startswith('data:image/svg+xml'))

    def test_unreadable_photo_without_name_uses_placeholder(self):
        partner = self.partner.copy({'name': False, 'type': 'delivery', 'parent_id': self.partner.id})
        with patch.object(type(self.Report), '_image_to_png', side_effect=OSError('broken')), \
                self.assertLogs('odoo.addons.print_subscription_id_card', level='WARNING'):
            uri = self.Report._get_partner_image(partner)
        self.assertTrue(uri.startswith('data:image/png;base64,'))

    def test_missing_partner(self):
        values = self.Report._get_report_values(None, data={'partner_id': 0})
        self.assertFalse(values['partner_image'])
        self.assertFalse(self.Report._get_report_values(None)['partner'])

    def test_salesman_can_print(self):
        salesman = new_test_user(self.env, login='id_card_salesman',
                                 groups='sales_team.group_sale_salesman_all_leads')
        order = self.order.with_user(salesman)
        report = self.env.ref('print_subscription_id_card.action_report_subscription_card')
        html = report.with_user(salesman)._render_qweb_html(
            report.report_name, None, data=self._data(order))[0].decode()
        self.assertIn('Anna Carter', html)
        self.assertTrue(self.env['ir.access'].search([
            ('model_id.model', '=', REPORT),
            ('group_id', '=', self.env.ref('sales_team.group_sale_salesman').id),
        ]))

    def test_report_html(self):
        report = self.env.ref('print_subscription_id_card.action_report_subscription_card')
        html = report._render_qweb_html(report.report_name, None, data=self._data())[0].decode()
        self.assertIn('o_subscription_id_card', html)
        self.assertIn('Anna Carter', html)
        self.assertIn('Gym Membership', html)
        self.assertIn('src="data:image/png;base64,', html)
