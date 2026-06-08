# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys(odoo@cybrosys.com)
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
from unittest.mock import patch
import requests
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError
from odoo import fields


@tagged('post_install', '-at_install')
class TestSurveyWhatsapp(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.survey = cls.env['survey.survey'].create({
            'title': 'Test Whatsapp Survey',
        })
        cls.country_us = cls.env['res.country'].search([('code', '=', 'US')], limit=1)
        if not cls.country_us:
            cls.country_us = cls.env['res.country'].create({
                'name': 'United States',
                'code': 'US',
                'phone_code': 1,
            })
        cls.partner = cls.env['res.partner'].create({
            'name': 'WhatsApp Recipient',
            'phone': '+1 (555) 123-4567',
            'country_id': cls.country_us.id,
        })
        cls.config_manager = cls.env['configuration.manager'].create({
            'instance': 'instance_123',
            'token': 'token_abc',
            'state': 'verified',
        })

    def test_01_compute_survey_start_url(self):
        """Test _compute_survey_start_url."""
        wizard = self.env['survey.whatsapp'].create({
            'survey_id': self.survey.id,
            'partner_ids': [(4, self.partner.id)],
            'answer_dead_line': fields.Date.today(),
        })
        self.assertTrue(wizard.survey_start_url)
        self.assertIn(self.survey.get_start_url(), wizard.survey_start_url)

    def test_02_action_send_msg_no_configuration(self):
        """Test action_send_msg raises ValidationError when no verified configuration exists."""
        self.config_manager.state = 'draft'
        wizard = self.env['survey.whatsapp'].create({
            'survey_id': self.survey.id,
            'partner_ids': [(4, self.partner.id)],
            'answer_dead_line': fields.Date.today(),
        })
        with self.assertRaises(ValidationError) as ctx:
            wizard.action_send_msg()
        self.assertIn("No verified WhatsApp configuration found", str(ctx.exception))

    def test_03_action_send_msg_no_phone(self):
        """Test action_send_msg raises ValidationError when recipient has no phone number."""
        self.config_manager.state = 'verified'
        partner_no_phone = self.env['res.partner'].create({
            'name': 'No Phone Partner',
            'phone': False,
        })
        wizard = self.env['survey.whatsapp'].create({
            'survey_id': self.survey.id,
            'partner_ids': [(4, partner_no_phone.id)],
            'answer_dead_line': fields.Date.today(),
        })
        with self.assertRaises(ValidationError) as ctx:
            wizard.action_send_msg()
        self.assertIn("No Message or not configured phone number", str(ctx.exception))

    def test_04_action_send_msg_success(self):
        """Test action_send_msg sending successfully."""
        self.config_manager.state = 'verified'
        wizard = self.env['survey.whatsapp'].create({
            'survey_id': self.survey.id,
            'partner_ids': [(4, self.partner.id)],
            'answer_dead_line': fields.Date.today(),
            'message': 'Please answer our survey:',
        })

        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.text = '{"sent": true}'

            res = wizard.action_send_msg()
            self.assertEqual(res['type'], 'ir.actions.client')
            self.assertEqual(res['tag'], 'display_notification')
            self.assertEqual(res['params']['type'], 'success')

            # Verify whatsapp.message record was created
            whatsapp_msg = self.env['whatsapp.message'].search([('to_user', '=', self.partner.phone)], limit=1)
            self.assertTrue(whatsapp_msg)
            self.assertEqual(whatsapp_msg.status, 'sent')
            self.assertEqual(whatsapp_msg.from_user, self.env.user)
            self.assertIn('Please answer our survey:', whatsapp_msg.body)

    def test_05_action_send_msg_http_error(self):
        """Test action_send_msg when Requests throws a ConnectionError."""
        self.config_manager.state = 'verified'
        wizard = self.env['survey.whatsapp'].create({
            'survey_id': self.survey.id,
            'partner_ids': [(4, self.partner.id)],
            'answer_dead_line': fields.Date.today(),
        })

        with patch('requests.post', side_effect=requests.exceptions.RequestException("Connection timed out")):
            with self.assertRaises(ValidationError) as ctx:
                wizard.action_send_msg()
            self.assertIn("Failed to send WhatsApp message", str(ctx.exception))
