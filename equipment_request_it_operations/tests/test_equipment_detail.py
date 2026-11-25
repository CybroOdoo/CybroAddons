# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Arshad Ali Pottengal (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestEquipmentDetail(common.TransactionCase):
    """Test suite for the equipment.detail model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create a product and use its auto-assigned uom_id (avoids
        # dependency on the 'uom' module's XML IDs being loaded)
        cls.product = cls.env['product.product'].create({
            'name': 'Equipment Test Product',
            'type': 'consu',
        })
        # Resolve the UoM from the product itself after creation
        cls.uom_unit = cls.product.uom_id

    # ------------------------------------------------------------------
    # _onchange_product_id
    # ------------------------------------------------------------------

    def test_onchange_product_id_sets_quantity_and_uom(self):
        """Changing product resets quantity to 1 and sets the product UoM."""
        detail = self.env['equipment.detail'].new({
            'product_id': self.product.id,
            'quantity': 5,
        })
        detail._onchange_product_id()
        self.assertEqual(detail.quantity, 1)
        self.assertEqual(detail.product_uom_id, self.product.uom_id)

    def test_onchange_product_id_no_product(self):
        """With no product set, onchange should not raise."""
        detail = self.env['equipment.detail'].new({})
        detail._onchange_product_id()
        # quantity stays at 1 (the field default)
        self.assertEqual(detail.quantity, 1)

    # ------------------------------------------------------------------
    # Create / basic field checks
    # ------------------------------------------------------------------

    def test_create_equipment_detail(self):
        """An equipment.detail record can be created and read back."""
        detail = self.env['equipment.detail'].create({
            'product_id': self.product.id,
            'quantity': 3,
            'description': 'Laptop for developer',
            'product_uom_id': self.uom_unit.id,
        })
        self.assertTrue(detail.id)
        self.assertEqual(detail.product_id, self.product)
        self.assertEqual(detail.quantity, 3)
        self.assertEqual(detail.description, 'Laptop for developer')

    def test_equipment_detail_default_quantity(self):
        """Default quantity for a new equipment.detail is 1."""
        detail = self.env['equipment.detail'].create({
            'product_id': self.product.id,
        })
        self.assertEqual(detail.quantity, 1)

    def test_equipment_detail_product_uom_set_via_onchange(self):
        """After calling onchange, product_uom_id matches the product's UoM."""
        detail = self.env['equipment.detail'].new({
            'product_id': self.product.id,
        })
        detail._onchange_product_id()
        self.assertEqual(detail.product_uom_id, self.product.uom_id)
