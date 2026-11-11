# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies
#    (<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
from odoo import Command
from odoo.tests import tagged

from .common import QualityCommon


@tagged('post_install', '-at_install', 'quality_assurance')
class TestPurchaseOrder(QualityCommon):

    def _create_po(self, product):
        return self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'picking_type_id': self.in_type.id,
            'order_line': [Command.create({
                'product_id': product.id,
                'product_qty': 5.0,
                'price_unit': 10.0,
            })],
        })

    def test_confirm_po_creates_receipt_with_quality_alert(self):
        po = self._create_po(self.product)
        po.button_confirm()
        self.assertEqual(len(po.picking_ids), 1)
        self.assertEqual(po.picking_ids.picking_type_id.code, 'incoming')
        alerts = self._get_alerts(po.picking_ids)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts.product_id, self.product)
        self.assertEqual(alerts.origin, po.picking_ids.name)

    def test_confirm_po_without_measures_creates_no_alert(self):
        po = self._create_po(self.product_plain)
        po.button_confirm()
        self.assertEqual(len(po.picking_ids), 1)
        self.assertFalse(self._get_alerts(po.picking_ids))

    def test_confirm_po_posts_note_on_order(self):
        po = self._create_po(self.product)
        po.button_confirm()
        notes = po.message_ids.filtered(
            lambda m: m.subtype_id == self.env.ref('mail.mt_note'))
        self.assertTrue(notes)
