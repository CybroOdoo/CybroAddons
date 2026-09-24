# -- coding: utf-8 --
###############################################################################
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
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests.common import SavepointCase, tagged


@tagged("post_install", "-at_install")
class TestContactsMassUpdate(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country = cls.env["res.country"].create({
            "name": "Mass Update Land",
            "code": "MU",
        })
        cls.empty_country = cls.env["res.country"].create({
            "name": "Empty Mass Update Land",
            "code": "ME",
        })
        cls.state = cls.env["res.country.state"].create({
            "name": "Mass Update State",
            "code": "MUS",
            "country_id": cls.country.id,
        })
        cls.old_tag = cls.env["res.partner.category"].create({
            "name": "Existing Test Tag",
        })
        cls.new_tag = cls.env["res.partner.category"].create({
            "name": "New Test Tag",
        })
        cls.replacement_tag = cls.env["res.partner.category"].create({
            "name": "Replacement Test Tag",
        })
        cls.salesperson = cls.env["res.users"].with_context(
            no_reset_password=True
        ).create({
            "name": "Mass Update Salesperson",
            "login": "mass_update_salesperson",
            "email": "mass_update_salesperson@example.com",
            "groups_id": [Command.link(cls.env.ref("base.group_user").id)],
        })
        cls.payment_term = cls.env["account.payment.term"].create({
            "name": "Mass Update Net 15",
        })
        cls.customer_partner = cls.env["res.partner"].create({
            "name": "Mass Update Customer",
            "customer_rank": 1,
            "country_id": cls.country.id,
            "state_id": cls.state.id,
            "category_id": [Command.link(cls.old_tag.id)],
        })
        cls.customer_partner_two = cls.env["res.partner"].create({
            "name": "Mass Update Customer Two",
            "customer_rank": 1,
            "country_id": cls.country.id,
            "state_id": cls.state.id,
        })
        cls.inactive_customer_partner = cls.env["res.partner"].create({
            "name": "Mass Update Archived Customer",
            "customer_rank": 1,
            "country_id": cls.country.id,
            "state_id": cls.state.id,
            "active": False,
        })
        cls.supplier_partner = cls.env["res.partner"].create({
            "name": "Mass Update Supplier",
            "supplier_rank": 1,
            "country_id": cls.country.id,
            "state_id": cls.state.id,
        })

    def test_default_get_prefills_partner_type_from_active_ids(self):
        wizard = self.env["contacts.mass.update"].with_context(
            active_ids=[self.customer_partner.id, self.supplier_partner.id]
        ).create({})

        self.assertEqual(wizard.partner_type, "both")

    def test_include_inactive_updates_count_and_preview(self):
        wizard = self.env["contacts.mass.update"].create({
            "partner_type": "customer",
            "filter_by_location": True,
            "country_ids": [Command.set([self.country.id])],
            "state_ids": [Command.set([self.state.id])],
        })

        self.assertEqual(wizard.partner_count, 2)
        self.assertEqual(wizard.preview_partner_ids, self.customer_partner | self.customer_partner_two)

        wizard.include_inactive = True

        self.assertEqual(wizard.partner_count, 3)
        self.assertEqual(
            wizard.preview_partner_ids,
            self.customer_partner | self.customer_partner_two | self.inactive_customer_partner,
        )

    def test_onchange_filter_by_location_clears_country_and_state(self):
        wizard = self.env["contacts.mass.update"].new({
            "partner_type": "all",
            "filter_by_location": True,
            "country_ids": [Command.set([self.country.id])],
            "state_ids": [Command.set([self.state.id])],
        })

        wizard.filter_by_location = False
        wizard._onchange_filter_by_location()

        self.assertFalse(wizard.country_ids)
        self.assertFalse(wizard.state_ids)

    def test_action_next_raises_when_no_partner_matches(self):
        wizard = self.env["contacts.mass.update"].create({
            "partner_type": "customer",
            "filter_by_location": True,
            "country_ids": [Command.set([self.empty_country.id])],
        })

        with self.assertRaises(UserError):
            wizard.action_next()

    def test_action_next_moves_to_confirm_with_preview_context(self):
        wizard = self.env["contacts.mass.update"].with_context(
            active_ids=[self.customer_partner.id, self.supplier_partner.id]
        ).create({
            "partner_type": "customer",
        })

        action = wizard.action_next()

        self.assertEqual(wizard.step, "confirm")
        self.assertEqual(action["res_id"], wizard.id)
        self.assertEqual(action["context"]["active_ids"], [self.customer_partner.id])

        back_action = wizard.action_back()
        self.assertEqual(wizard.step, "select")
        self.assertEqual(back_action["res_id"], wizard.id)

    def test_action_update_partner_appends_tags_and_updates_fields(self):
        wizard = self.env["contacts.mass.update"].with_context(
            active_ids=[self.customer_partner.id, self.customer_partner_two.id]
        ).create({
            "partner_type": "customer",
            "tag_ids": [Command.set([self.new_tag.id])],
            "user_id": self.salesperson.id,
            "property_payment_term_id": self.payment_term.id,
            "company_id": self.env.company.id,
        })

        action = wizard.action_update_partner()
        self.customer_partner.invalidate_recordset()
        self.customer_partner_two.invalidate_recordset()

        self.assertEqual(action["tag"], "display_notification")
        self.assertIn(self.old_tag, self.customer_partner.category_id)
        self.assertIn(self.new_tag, self.customer_partner.category_id)
        self.assertEqual(self.customer_partner.user_id, self.salesperson)
        self.assertEqual(self.customer_partner.property_payment_term_id, self.payment_term)
        self.assertEqual(self.customer_partner.company_id, self.env.company)
        self.assertEqual(self.customer_partner_two.user_id, self.salesperson)
        self.assertEqual(self.customer_partner_two.property_payment_term_id, self.payment_term)
        self.assertEqual(self.customer_partner_two.company_id, self.env.company)

    def test_action_update_partner_replaces_existing_tags(self):
        wizard = self.env["contacts.mass.update"].with_context(
            active_ids=[self.customer_partner.id]
        ).create({
            "partner_type": "customer",
            "tag_ids": [Command.set([self.replacement_tag.id])],
            "replace_tags": True,
        })

        wizard.action_update_partner()
        self.customer_partner.invalidate_recordset()

        self.assertEqual(self.customer_partner.category_id, self.replacement_tag)
