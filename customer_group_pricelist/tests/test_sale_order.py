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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo.fields import Command
from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestSaleOrderCustomerGroup(TransactionCase):
    """Test cases for sale.order pricelist assignment based on customer group."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.env['ir.default'].set('res.partner', 'autopost_bills', 'never')

        cls.CustomerGroup = cls.env['customer.group']
        cls.SaleOrder = cls.env['sale.order']
        cls.Partner = cls.env['res.partner']
        cls.Pricelist = cls.env['product.pricelist']

        # Setup test pricelists
        cls.pricelist_default = cls.Pricelist.create({
            'name': 'Default Public Pricelist',
        })
        cls.pricelist_vip = cls.Pricelist.create({
            'name': 'VIP Pricelist',
        })
        cls.pricelist_wholesale = cls.Pricelist.create({
            'name': 'Wholesale Pricelist',
        })

        cls.partner_vip = cls.Partner.create({
            'name': 'VIP Partner',
            'email': 'vip@test.com',
            'specific_property_product_pricelist': cls.pricelist_default.id,
        })
        cls.partner_wholesale = cls.Partner.create({
            'name': 'Wholesale Partner',
            'email': 'wholesale@test.com',
            'specific_property_product_pricelist': cls.pricelist_default.id,
        })
        cls.partner_regular = cls.Partner.create({
            'name': 'Regular Partner',
            'email': 'regular@test.com',
            'specific_property_product_pricelist': cls.pricelist_default.id,
        })



        # Setup customer groups
        cls.group_vip = cls.CustomerGroup.create({
            'name': 'VIP Customers Group',
            'contact_ids': [Command.set([cls.partner_vip.id])],
            'pricelist_id': cls.pricelist_vip.id,
        })
        cls.group_wholesale = cls.CustomerGroup.create({
            'name': 'Wholesale Customers Group',
            'contact_ids': [Command.set([cls.partner_wholesale.id])],
            'pricelist_id': cls.pricelist_wholesale.id,
        })

    def _trigger_onchange_partner_id(self, order):
        """Invoke customer_group_pricelist onchange logic directly on order."""
        from odoo.addons.customer_group_pricelist.models.sale_order import SaleOrder
        SaleOrder._onchange_partner_id(order)

    def test_01_onchange_partner_id_sets_group_pricelist(self):
        """Test that selecting a partner belonging to a customer group assigns its pricelist."""
        order = self.SaleOrder.new({
            'partner_id': self.partner_vip.id,
            'pricelist_id': self.pricelist_default.id,
        })
        self._trigger_onchange_partner_id(order)

        self.assertEqual(
            order.pricelist_id,
            self.pricelist_vip,
            "Pricelist should be updated to VIP pricelist from the customer group"
        )

    def test_02_onchange_partner_id_regular_partner_unaffected(self):
        """Test that selecting a partner without a customer group does not change pricelist to a group pricelist."""
        order = self.SaleOrder.new({
            'partner_id': self.partner_regular.id,
            'pricelist_id': self.pricelist_default.id,
        })
        self._trigger_onchange_partner_id(order)

        self.assertEqual(
            order.pricelist_id,
            self.pricelist_default,
            "Pricelist should remain default for partner not associated with any customer group"
        )

    def test_03_partner_switching(self):
        """Test dynamic switching of partner_id on the sale order."""
        order = self.SaleOrder.new({
            'partner_id': self.partner_regular.id,
            'pricelist_id': self.pricelist_default.id,
        })
        self._trigger_onchange_partner_id(order)
        self.assertEqual(order.pricelist_id, self.pricelist_default)

        # Switch to VIP partner
        order.partner_id = self.partner_vip
        self._trigger_onchange_partner_id(order)
        self.assertEqual(order.pricelist_id, self.pricelist_vip)

        # Switch to Wholesale partner
        order.partner_id = self.partner_wholesale
        self._trigger_onchange_partner_id(order)
        self.assertEqual(order.pricelist_id, self.pricelist_wholesale)

    def test_04_form_view_onchange_integration(self):
        """Test onchange triggering automatically through the sale order form view."""
        with Form(self.SaleOrder) as order_form:
            order_form.partner_id = self.partner_vip
            self.assertEqual(
                order_form.pricelist_id,
                self.pricelist_vip,
                "Form view onchange should automatically set pricelist from customer group"
            )
            sale_order = order_form.save()

        self.assertEqual(sale_order.pricelist_id, self.pricelist_vip)

    def test_05_multiple_contacts_in_same_group(self):
        """Test that multiple contacts in the same customer group both receive the group pricelist."""
        partner_vip_2 = self.Partner.create({
            'name': 'Second VIP Partner',
            'email': 'vip2@test.com',
            'property_product_pricelist': self.pricelist_default.id,
        })
        self.group_vip.write({
            'contact_ids': [Command.link(partner_vip_2.id)],
        })

        order = self.SaleOrder.new({
            'partner_id': partner_vip_2.id,
            'pricelist_id': self.pricelist_default.id,
        })
        self._trigger_onchange_partner_id(order)

        self.assertEqual(
            order.pricelist_id,
            self.pricelist_vip,
            "Second VIP partner should also receive VIP pricelist from the group"
        )

    def test_06_customer_group_without_pricelist(self):
        """Test customer group where pricelist_id is False."""
        partner_no_pl = self.Partner.create({
            'name': 'Partner No Pricelist Group',
            'email': 'nopl@test.com',
            'specific_property_product_pricelist': self.pricelist_default.id,
        })
        self.CustomerGroup.create({
            'name': 'Group Without Pricelist',
            'contact_ids': [Command.set([partner_no_pl.id])],
            'pricelist_id': False,
        })

        order = self.SaleOrder.new({
            'partner_id': partner_no_pl.id,
            'pricelist_id': self.pricelist_default.id,
        })
        self._trigger_onchange_partner_id(order)

        self.assertEqual(
            order.pricelist_id,
            self.pricelist_default,
            "Pricelist should remain default when group has no pricelist"
        )

    def test_07_partner_removed_from_group(self):
        """Test that removing a partner from the customer group stops setting the group pricelist."""
        self.group_vip.write({
            'contact_ids': [Command.unlink(self.partner_vip.id)],
        })

        order = self.SaleOrder.new({
            'partner_id': self.partner_vip.id,
            'pricelist_id': self.pricelist_default.id,
        })
        self._trigger_onchange_partner_id(order)

        self.assertEqual(
            order.pricelist_id,
            self.pricelist_default,
            "Removed partner should no longer get the VIP pricelist applied"
        )

    def test_08_create_backend_and_import(self):
        """Test that pricelist is computed automatically during backend create / data import without UI onchange."""
        order_vip = self.SaleOrder.create({
            'partner_id': self.partner_vip.id,
        })
        self.assertEqual(
            order_vip.pricelist_id,
            self.pricelist_vip,
            "Pricelist should be computed on record create without UI onchange"
        )

        order_regular = self.SaleOrder.create({
            'partner_id': self.partner_regular.id,
        })
        self.assertNotEqual(
            order_regular.pricelist_id,
            self.pricelist_vip,
            "Regular partner should not receive VIP pricelist on record create"
        )
        self.assertEqual(
            order_regular.pricelist_id,
            self.partner_regular.property_product_pricelist,
            "Regular partner should retain default pricelist on record create"
        )

    def test_09_multi_record_batch_creation(self):
        """Test multi-record safety by creating multiple orders in a single batch."""
        orders = self.SaleOrder.create([
            {'partner_id': self.partner_vip.id},
            {'partner_id': self.partner_wholesale.id},
            {'partner_id': self.partner_regular.id},
        ])
        self.assertEqual(len(orders), 3)
        self.assertEqual(orders[0].pricelist_id, self.pricelist_vip)
        self.assertEqual(orders[1].pricelist_id, self.pricelist_wholesale)
        self.assertNotEqual(orders[2].pricelist_id, self.pricelist_vip)
        self.assertEqual(orders[2].pricelist_id, self.partner_regular.property_product_pricelist)

    def test_10_compute_pricelist_id_direct_call(self):
        """Test calling _compute_pricelist_id directly on single and multiple records."""
        order_vip = self.SaleOrder.new({'partner_id': self.partner_vip.id})
        order_wholesale = self.SaleOrder.new({'partner_id': self.partner_wholesale.id})
        orders = order_vip + order_wholesale

        orders._compute_pricelist_id()

        self.assertEqual(order_vip.pricelist_id, self.pricelist_vip)
        self.assertEqual(order_wholesale.pricelist_id, self.pricelist_wholesale)



