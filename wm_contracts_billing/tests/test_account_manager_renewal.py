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
from datetime import timedelta

from odoo import fields
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestAccountManagerRenewal(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer Renewal',
            'email': 'customer_renewal@example.com',
        })
        cls.test_user = cls.env['res.users'].create({
            'name': 'Account Manager User',
            'login': 'account_mgr_user',
            'email': 'account_mgr@example.com',
        })
        cls.sla = cls.env['wm.sla'].create({
            'name': 'Standard Test SLA',
        })

    def test_01_contract_user_id_default(self):
        """Test user_id default value on direct contract creation."""
        contract = self.env['wm.partner.contract'].create({
            'partner_id': self.partner.id,
            'from_date': fields.Date.today(),
            'to_date': fields.Date.today() + timedelta(days=365),
            'frequency': 'monthly',
            'no_of_frequency': 1,
            'billing_basis': 'per_collection',
            'fixed_price': 100.0,
            'max_weight': 500.0,
            'overweight_price': 10.0,
            'sla_id': self.sla.id,
        })
        self.assertEqual(contract.user_id, self.env.user)

    def test_02_lead_conversion_user_id_precedence(self):
        """Test wizard sets user_id from quotation -> lead -> env.user."""
        lead = self.env['crm.lead'].create({
            'name': 'Opportunity for Account Manager Test',
            'partner_id': self.partner.id,
            'user_id': self.test_user.id,
        })

        wizard = self.env['wm.lead.conversion.wizard'].create({
            'lead_id': lead.id,
            'partner_id': self.partner.id,
            'contract_from_date': fields.Date.today(),
            'contract_to_date': fields.Date.today() + timedelta(days=365),
            'frequency': 'weekly',
            'no_of_frequency': 1,
            'billing_basis': 'per_collection',
            'sla_id': self.sla.id,
            'fixed_price': 150.0,
            'max_weight': 400.0,
            'overweight_price': 15.0,
        })
        res = wizard.action_confirm_conversion()
        contract_id = res.get('res_id')
        contract = self.env['wm.partner.contract'].browse(contract_id)
        self.assertEqual(contract.user_id, self.test_user)

    def test_03_cron_renewal_reminders(self):
        """Test renewal reminder cron creates activity for expiring contracts."""
        # Set system parameter to 15 days
        self.env['ir.config_parameter'].sudo().set_param(
            'wm_contracts_billing.renewal_reminder_days', '15'
        )

        today = fields.Date.today()
        expiring_date = today + timedelta(days=15)

        contract = self.env['wm.partner.contract'].create({
            'partner_id': self.partner.id,
            'user_id': self.test_user.id,
            'from_date': today - timedelta(days=350),
            'to_date': expiring_date,
            'frequency': 'monthly',
            'no_of_frequency': 1,
            'billing_basis': 'per_collection',
            'fixed_price': 100.0,
            'max_weight': 500.0,
            'overweight_price': 10.0,
            'sla_id': self.sla.id,
            'state': 'ongoing',
        })

        self.env['wm.partner.contract']._cron_contract_renewal_reminders()

        activity = self.env['mail.activity'].search([
            ('res_model', '=', 'wm.partner.contract'),
            ('res_id', '=', contract.id),
        ])
        self.assertTrue(activity, "Activity should be created for expiring contract")
        self.assertEqual(activity.user_id, self.test_user)
        self.assertIn(contract.name, activity.summary)
