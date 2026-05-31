# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools.safe_eval import safe_eval


@tagged('post_install', '-at_install')
class TestPosCustomerRestrict(TransactionCase):
    """Test POS customer availability restrictions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_model = cls.env['res.partner']

    def test_partner_not_available_in_pos_by_default(self):
        """Test standard partner is restricted from POS by default."""

        partner = self.partner_model.create({
            'name': 'Restricted POS Customer',
        })

        self.assertFalse(
            partner.is_available_in_pos
        )

    def test_pos_action_default_customer_available(self):
        """Test POS action sets customer availability default to True."""

        action = self.env.ref(
            'point_of_sale.res_partner_action_edit_pos',
            raise_if_not_found=False
        )

        if not action:
            self.skipTest(
                "POS partner action not found."
            )

        action_context = safe_eval(
            action.context or "{}"
        )

        defaults = self.partner_model.with_context(
            **action_context
        ).default_get([
            'is_available_in_pos'
        ])

        self.assertTrue(
            defaults.get('is_available_in_pos')
        )

    def test_pos_data_fields_include_availability(self):
        """Test POS data fields include availability field."""

        fields = self.partner_model._load_pos_data_fields(
            False
        )

        self.assertIn(
            'is_available_in_pos',
            fields
        )

    def test_partner_manual_pos_availability(self):
        """Test manually enabling POS availability."""

        partner = self.partner_model.create({
            'name': 'Available POS Customer',
            'is_available_in_pos': True,
        })

        self.assertTrue(
            partner.is_available_in_pos
        )