# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Surya Gayathry TA (odoo@cybrosys.com)
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
###############################################################################

from odoo.tests.common import TransactionCase

class TestProductModels(TransactionCase):
    def setUp(self):
        super(TestProductModels, self).setUp()
        self.brand = self.env['product.brand'].create({
            'name': 'Test Brand'
        })
        self.product_tmpl = self.env['product.template'].create({
            'name': 'Test Product Template',
            'brand_id': self.brand.id,
        })
        self.product = self.env['product.product'].search([('product_tmpl_id', '=', self.product_tmpl.id)], limit=1)

    def test_product_brand_count(self):
        # Trigger compute
        self.brand.get_count_products()
        self.assertEqual(int(self.brand.product_count), 1)

    def test_action_get_wo_description(self):
        # Product template report action
        res_tmpl = self.product_tmpl.with_context(discard_logo_check=True).action_get_wo_description()
        self.assertEqual(res_tmpl['type'], 'ir.actions.report')
        self.assertEqual(res_tmpl['report_name'], 'all_in_one_inventory_kit.report_product_stock_template')
        
        # Product report action
        res_prod = self.product.with_context(discard_logo_check=True).action_get_wo_description()
        self.assertEqual(res_prod['type'], 'ir.actions.report')
        self.assertEqual(res_prod['report_name'], 'all_in_one_inventory_kit.report_product_stock_template')

    def test_onchange_cw_uom_id(self):
        uom_kg = self.env.ref('uom.product_uom_kgm')
        uom_g = self.env.ref('uom.product_uom_gram')
        uom_unit = self.env.ref('uom.product_uom_unit')

        self.product_tmpl.uom_id = uom_kg
        self.product_tmpl.cw_uom_id = uom_g

        # Same category test
        self.product_tmpl._onchange_cw_uom_id()
        self.assertEqual(self.product_tmpl.average_cw_qty, 1000.0) # 1 kg = 1000 g

        # Different category test
        self.product_tmpl.uom_id = uom_unit
        self.product_tmpl._onchange_cw_uom_id()
        self.assertEqual(self.product_tmpl.average_cw_qty, 1.0)
