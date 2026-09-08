# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
import logging

from odoo.tests import tagged, TransactionCase


_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'wm_collection')
class TestCategoryBatchCreation(TransactionCase):
    """Unit tests verifying automated batch creation from categorized collection orders."""

    @classmethod
    def setUpClass(cls):
        """
        Set up test class fixtures and environment.
        """
        super().setUpClass()
        cls.category_paper = cls.env['wm.waste.category'].create({
            'name': 'Test Paper Stream',
            'code': 'TPAPER',
            'price': 0.50,
            'auto_create_batches_on_collection': True,
        })
        cls.category_metal = cls.env['wm.waste.category'].create({
            'name': 'Test Metal Stream',
            'code': 'TMETAL',
            'price': 1.50,
            'auto_create_batches_on_collection': True,
        })
        cls.product_cardboard = cls.env['product.product'].create({
            'name': 'Test Cardboard Box',
            'is_waste_material': True,
            'wm_waste_category_id': cls.category_paper.id,
            'list_price': 0.60,
        })
        cls.product_scrap = cls.env['product.product'].create({
            'name': 'Test Scrap Metal',
            'is_waste_material': True,
            'wm_waste_category_id': cls.category_metal.id,
            'list_price': 1.80,
        })
        cls.partner = cls.env['res.partner'].create({'name': 'Test Generator Partner'})
        cls.point = cls.env['wm.collection.point'].create({
            'name': 'Test Collection Facility',
            'partner_id': cls.partner.id,
        })
        cls.route = cls.env['wm.route'].create({'name': 'Test Collection Route'})
        brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Test Fleet Brand'})
        model = cls.env['fleet.vehicle.model'].create({'name': 'Truck Model', 'brand_id': brand.id})
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': model.id,
            'driver_id': cls.partner.id,
            'license_plate': 'TEST-BATCH-01',
        })

    def test_category_batch_creation(self):
        """
        Completing a collection order with lines in 2 different categories
        auto-creates 2 waste batches.
        """
        order = self.env['wm.collection.order'].create({
            'name': 'ORD-CAT-TEST-001',
            'partner_id': self.partner.id,
            'collection_point_id': self.point.id,
            'route_id': self.route.id,
            'vehicle_id': self.vehicle.id,
            'driver_id': self.partner.id,
            'company_id': self.env.company.id,
        })
        self.env['wm.collection.order.line'].create({
            'order_id': order.id,
            'category_id': self.category_paper.id,
            'product_id': self.product_cardboard.id,
            'weight': 120.0,
        })
        self.env['wm.collection.order.line'].create({
            'order_id': order.id,
            'category_id': self.category_metal.id,
            'product_id': self.product_scrap.id,
            'weight': 80.0,
        })

        order.action_dispatch()
        order.action_start()
        order.action_complete()

        self.assertEqual(order.state, 'completed')
        batches = order.waste_batch_ids
        self.assertEqual(len(batches), 2, "Completing order with 2 category lines must create exactly 2 waste.batch records")

        paper_batch = batches.filtered(lambda b: b.category_id == self.category_paper)
        metal_batch = batches.filtered(lambda b: b.category_id == self.category_metal)

        self.assertTrue(paper_batch, "A batch for the Paper category must exist")
        self.assertTrue(metal_batch, "A batch for the Metal category must exist")

        self.assertEqual(paper_batch.draft_quantity, 120.0)
        self.assertEqual(metal_batch.draft_quantity, 80.0)
        self.assertEqual(paper_batch.batch_type, 'collection')
        self.assertEqual(paper_batch.sorting_status, 'unsorted')

        _logger.info('PASS: test_category_batch_creation')
