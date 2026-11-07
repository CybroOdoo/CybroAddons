# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
# ######################################################################
import logging
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)

class TestAdultDaycare(TransactionCase):
    """Tests for the adult day care center module."""

    def setUp(self):
        super().setUp()
        _logger.info("Setting up adult_daycare_center test data")
        # 1. Setup Partner
        self.partner = self.env['res.partner'].create({
            'name': 'Test Senior',
            'is_adult_member': True,
        })

        # 2. Setup Lead Request
        self.lead = self.env['crm.lead'].create({
            'name': 'Daycare Inquiry',
            'partner_id': self.partner.id,
            'medicare': 123456,
            'medicaid': 654321,
            'transportation': 'public_transport',
            'special_diet': 'yes',
            'diet_detail': 'Low sugar'
        })

        # 3. Setup Activity & Product
        self.activity_type = self.env['activity.type'].create({
            'name': 'Yoga'
        })
        self.product_template = self.env['product.template'].create({
            'name': 'Yoga Class',
            'is_adult_activity': True,
            'list_price': 50.0,
        })
        # Product template automatically creates product.product
        self.product = self.env['product.product'].search([
            ('product_tmpl_id', '=', self.product_template.id)
        ], limit=1)

        # 4. Assign Activity to Partner
        self.daycare_activity = self.env['daycare.activities'].create({
            'activity_id': self.activity_type.id,
            'product_id': self.product_template.id,
            'res_partner_id': self.partner.id,
            'time_in': 9.0,
            'time_out': 11.0,
        })

    def test_01_crm_lead_update_adult_info(self):
        """ Test if crm.lead updates the corresponding res.partner correctly """
        _logger.info("Started adult_daycare_center test_01_crm_lead_update_adult_info")

        self.lead.action_updt_adult_info()

        # Verify partner fields are updated
        self.assertEqual(self.partner.medicare_no, 123456, "Medicare number was not synced correctly")
        self.assertEqual(self.partner.medicaid_no, 654321, "Medicaid number was not synced correctly")
        self.assertEqual(self.partner.transportation, 'public_transport', "Transportation was not synced correctly")
        self.assertEqual(self.partner.special_diet, 'yes', "Special diet was not synced correctly")
        self.assertEqual(self.partner.diet_detail, 'Low sugar', "Diet details were not synced correctly")
        self.assertTrue(self.partner.is_customer, "is_customer should be True")
        self.assertTrue(self.partner.is_adult_member, "is_adult_member should be True")
        _logger.info("Completed adult_daycare_center test_01_crm_lead_update_adult_info")

    def test_02_res_partner_onchange_is_adult_member(self):
        """ Test the onchange method for is_adult_member on res.partner """
        _logger.info("Started adult_daycare_center test_02_res_partner_onchange_is_adult_member")
        partner2 = self.env['res.partner'].create({
            'name': 'Another Senior'
        })

        # Simulate onchange to True
        partner2.is_adult_member = True
        partner2._onchange_is_adult_member()
        self.assertTrue(partner2.is_customer, "is_customer should be True when is_adult_member is True")

        # Simulate onchange to False
        partner2.is_adult_member = False
        partner2._onchange_is_adult_member()
        self.assertFalse(partner2.is_customer, "is_customer should be False when is_adult_member is False")
        _logger.info("Completed adult_daycare_center test_02_res_partner_onchange_is_adult_member")

    def test_03_sale_order_onchange_adult_person_id(self):
        """ Test if selecting an adult_person_id populates the sale order lines """
        _logger.info("Started adult_daycare_center test_03_sale_order_onchange_adult_person_id")

        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })

        # Assign the adult person which should trigger the onchange
        sale_order.adult_person_id = self.partner.id
        sale_order._onchange_adult_person_id()

        # Verify order lines are populated correctly from the daycare_activities_ids
        self.assertEqual(len(sale_order.order_line), 1, "There should be exactly 1 order line created")
        self.assertEqual(sale_order.order_line[0].product_id.id, self.product.id,
                         "The order line product should match the daycare activity product")
        self.assertEqual(sale_order.order_line[0].product_uom_qty, 1.0, "The generated order line quantity should be 1")
        _logger.info("Completed adult_daycare_center test_03_sale_order_onchange_adult_person_id")

    def test_04_sale_order_onchange_replaces_existing_lines(self):
        """ Changing the adult person must replace previously loaded lines """
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        sale_order.adult_person_id = self.partner.id
        sale_order._onchange_adult_person_id()
        sale_order._onchange_adult_person_id()
        self.assertEqual(len(sale_order.order_line), 1,
                         "Lines should be replaced, not duplicated")
