# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPosDataLoading(TransactionCase):
    """Tests that lots are loaded into the POS session."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = (
            cls.env['pos.config'].search([('company_id', '=', cls.env.company.id)], limit=1)
            or cls.env['pos.config'].create({'name': 'Lot Expiry Test POS'})
        )
        cls.product = cls.env['product.product'].create({
            'name': 'POS Lot Test Product',
            'is_storable': True,
            'tracking': 'lot',
        })
        cls.lot = cls.env['stock.lot'].create({
            'name': 'POS-LOT-001',
            'product_id': cls.product.id,
            'company_id': cls.env.company.id,
        })

    def test_stock_lot_is_loaded_in_pos(self):
        """``stock.lot`` is part of the models loaded by the POS session."""
        models = self.env['pos.session']._load_pos_data_models(self.config)
        self.assertIn('stock.lot', models)

    def test_stock_lot_is_added_only_once(self):
        """The model list has no duplicated ``stock.lot`` entry."""
        models = self.env['pos.session']._load_pos_data_models(self.config)
        self.assertEqual(models.count('stock.lot'), 1)

    def test_stock_lot_uses_pos_load_mixin(self):
        """``stock.lot`` inherits the POS loading mixin."""
        self.assertIsInstance(self.env['stock.lot'], self.env.registry['pos.load.mixin'])

    def test_stock_lot_pos_fields(self):
        """Only the name and the product are sent to the POS."""
        fields_list = self.env['stock.lot']._load_pos_data_fields(self.config)
        self.assertCountEqual(fields_list, ['name', 'product_id'])

    def test_stock_lot_pos_domain(self):
        """The loading domain does not restrict the lots."""
        self.assertEqual(self.env['stock.lot']._load_pos_data_domain({}), [])

    def test_stock_lot_pos_read(self):
        """Reading the lot for the POS returns the configured fields."""
        data = self.env['stock.lot']._load_pos_data_read(self.lot, self.config)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'POS-LOT-001')
        self.assertEqual(data[0]['product_id'], self.product.id)
        self.assertNotIn('expiration_date', data[0])
