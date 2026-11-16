# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (
#    OPL-1) It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
#############################################################################
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestStockPickingType(TransactionCase):
    """Test cases for models/stock_picking_type.py."""

    def test_display_name_field_attributes(self):
        """display_name on stock.picking.type should be stored and editable."""
        field = self.env['stock.picking.type']._fields['display_name']
        self.assertTrue(field.store)
        self.assertFalse(field.readonly)
        self.assertEqual(field.string, 'Display name')
        self.assertEqual(field.help, 'Name which is to display')

    def test_create_and_update_picking_type_display_name(self):
        """display_name on stock.picking.type can be written and persisted."""
        picking_type = self.env['stock.picking.type'].create({
            'name': 'Custom Test Receipt',
            'code': 'incoming',
            'sequence_code': 'CTR',
        })
        picking_type.write({'display_name': 'Stored Picking Type Name'})
        self.assertEqual(picking_type.display_name, 'Stored Picking Type Name')

