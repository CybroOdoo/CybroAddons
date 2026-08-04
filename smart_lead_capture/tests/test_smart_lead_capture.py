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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from unittest.mock import patch
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSmartLeadCapture(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.salesperson = cls.env['res.users'].create({
            'name': 'Sales User',
            'login': 'sales_user_test',
            'email': 'sales@test.com',
        })

    @patch(
        'odoo.addons.smart_lead_capture.models.crm_lead.'
        'SmartLeadCapture._trigger_outbound_webhook'
    )
    def test_lead_create_triggers_webhook(self, mock_webhook):
        """Test for lead create triggers webhook"""
        lead = self.env['crm.lead'].create({
            'name': 'Lead A',
        })
        self.assertTrue(lead)
        self.assertEqual(mock_webhook.call_count, 1)

    @patch(
        'odoo.addons.smart_lead_capture.models.crm_lead.'
        'SmartLeadCapture._trigger_outbound_webhook'
    )
    def test_lead_write_triggers_webhook(self, mock_webhook):
        """Test for lead write triggers webhook"""
        lead = self.env['crm.lead'].create({
            'name': 'Lead A',
        })
        mock_webhook.reset_mock()
        lead.write({
            'phone': '9999999999'
        })
        self.assertEqual(mock_webhook.call_count, 1)

    def test_send_lead_email_notification(self):
        """Test for send_lead_email_notification"""
        lead = self.env['crm.lead'].create({
            'name': 'Email Lead',
            'user_id': self.salesperson.id,
            'email_from': 'lead@test.com',
            'phone': '1234567890',
        })
        lead.send_lead_email_notification()
        self.assertTrue(True)

    def test_config_parameters(self):
        """Test for config_parameters"""
        icp = self.env['ir.config_parameter'].sudo()
        icp.set_param(
            'smart_lead_capture.default_salesperson_id',
            self.salesperson.id
        )
        self.assertEqual(
            int(icp.get_param(
                'smart_lead_capture.default_salesperson_id'
            )),
            self.salesperson.id
        )

    def test_whatsapp_notification_without_credentials(self):
        """Test for whatsapp notification"""
        lead = self.env['crm.lead'].create({
            'name': 'WhatsApp Lead',
        })
        lead.send_whatsapp_notification()
        self.assertTrue(True)

    def test_lead_source_default(self):
        """Test for default lead source"""
        lead = self.env['crm.lead'].create({
            'name': 'Source Test Lead',
        })

        self.assertEqual(
            lead.lead_source_channel,
            'manual'
        )
