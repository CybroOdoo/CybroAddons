# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests.common import TransactionCase


class TestMaterialUsed(TransactionCase):
    """Test cases for the material.used model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Reuse an existing product to avoid cross-module NOT NULL column issues
        cls.product = cls.env['product.product'].search([], limit=1)

    def setUp(self):
        super().setUp()
        # Set up a minimal workshop record to link materials to
        brand = self.env['fleet.vehicle.model.brand'].create(
            {'name': 'Nissan'})
        model = self.env['fleet.vehicle.model'].create({
            'name': 'Altima',
            'brand_id': brand.id,
        })
        fleet_vehicle = self.env['fleet.vehicle'].create(
            {'model_id': model.id})
        self.vehicle_detail = self.env['vehicle.details'].create(
            {'vehicle_id': fleet_vehicle.id})
        self.stage = self.env['worksheet.stages'].create(
            {'name': 'In Progress', 'sequence': 2})
        self.workshop = self.env['car.workshop'].create({
            'name': 'Full Service',
            'vehicle_id': self.vehicle_detail.id,
            'stage_id': self.stage.id,
        })

    def test_create_material_used(self):
        """Test creating a material.used record with valid data."""
        material = self.env['material.used'].create({
            'material_product_id': self.product.id,
            'quantity': 4,
            'price': 25.0,
            'material_id': self.workshop.id,
        })
        self.assertEqual(material.material_product_id.id, self.product.id,
                         "Product should be linked correctly.")
        self.assertEqual(material.quantity, 4,
                         "Quantity should match.")
        self.assertEqual(material.price, 25.0,
                         "Price should match.")


    def test_material_product_required(self):
        """Test that material_product_id is required."""
        self.assertTrue(self.env['material.used']._fields['material_product_id'].required)


    def test_default_quantity(self):
        """Test that default quantity is 1."""
        material = self.env['material.used'].create({
            'material_product_id': self.product.id,
            'material_id': self.workshop.id,
        })
        self.assertEqual(material.quantity, 1,
                         "Default quantity should be 1.")


    def test_onchange_material_product_id(self):
        """Test that _onchange_material_product_id sets the price from lst_price."""
        material = self.env['material.used'].new({
            'material_product_id': self.product.id,
            'material_id': self.workshop.id,
        })
        material._onchange_material_product_id()
        self.assertEqual(material.price, self.product.lst_price,
                         "Price should be populated from product's lst_price.")


    def test_company_id_default(self):
        """Test that company_id defaults to the current user's company."""
        material = self.env['material.used'].create({
            'material_product_id': self.product.id,
            'material_id': self.workshop.id,
        })
        self.assertEqual(material.company_id.id, self.env.company.id,
                         "company_id should default to the current company.")


    def test_currency_id_related_to_company(self):
        """Test that currency_id is correctly related to the company's currency."""
        material = self.env['material.used'].create({
            'material_product_id': self.product.id,
            'material_id': self.workshop.id,
        })
        self.assertEqual(material.currency_id.id,
                         self.env.company.currency_id.id,
                         "currency_id should match the company's currency.")


    def test_update_material_used(self):
        """Test updating a material.used record."""
        material = self.env['material.used'].create({
            'material_product_id': self.product.id,
            'quantity': 1,
            'price': 25.0,
            'material_id': self.workshop.id,
        })
        material.write({'quantity': 5, 'price': 22.0})
        self.assertEqual(material.quantity, 5)
        self.assertEqual(material.price, 22.0)


    def test_delete_material_used(self):
        """Test deleting a material.used record."""
        material = self.env['material.used'].create({
            'material_product_id': self.product.id,
            'material_id': self.workshop.id,
        })
        material_id = material.id
        material.unlink()
        self.assertFalse(
            self.env['material.used'].search([('id', '=', material_id)]),
            "Material record should be deleted.")

    def test_compute_is_invoiced(self):
        """Test the computation of is_invoiced based on invoice_line_ids."""
        material = self.env['material.used'].create({
            'material_product_id': self.product.id,
            'material_id': self.workshop.id,
        })
        # Simulate linking an invoice line
        move = self.env['account.move'].create({'move_type': 'out_invoice'})
        line = self.env['account.move.line'].create({
            'move_id': move.id,
            'name': 'Test Material',
            'product_id': self.product.id,
            'account_id': self.env['account.journal'].search([('type', '=', 'sale')], limit=1).default_account_id.id
        })
        material.invoice_line_ids = [(4, line.id)]
        self.assertTrue(material.is_invoiced)
        
        move.button_cancel()
        self.assertFalse(material.is_invoiced)
