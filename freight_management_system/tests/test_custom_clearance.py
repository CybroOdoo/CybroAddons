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
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import FreightCommon


@tagged('post_install', '-at_install')
class TestCustomClearance(FreightCommon):

    def test_01_custom_clearance_actions(self):
        """Test custom clearance actions"""
        order = self._create_order()
        clearance = self.env['custom.clearance'].create({
            'freight_id': order.id,
            'agent_id': self.partner_agent.id,
        })
        self.assertEqual(clearance.name, 'CC - ' + order.name)
        clearance._onchange_freight_id()
        self.assertEqual(clearance.loading_port_id, self.port_loading)
        self.assertEqual(clearance.discharging_port_id,
                         self.port_discharging)

        clearance.action_confirm()
        self.assertEqual(clearance.state, 'confirm')
        with self.assertRaises(ValidationError):
            clearance.action_confirm()

        action = clearance.action_revision()
        self.assertEqual(action['res_model'], 'custom.clearance.revision')
        self.assertEqual(action['context']['default_custom_id'],
                         clearance.id)

    def test_02_revision_wizard_escapes_reason(self):
        """The reason is escaped in the notification and mails are queued"""
        order = self._create_order()
        clearance = self.env['custom.clearance'].create({
            'freight_id': order.id,
            'agent_id': self.partner_agent.id,
        })
        clearance.action_confirm()
        reason = '<script>alert(1)</script>'
        wizard = self.env['custom.clearance.revision'].create({
            'custom_id': clearance.id,
            'name': reason,
        })
        wizard.action_create_revision()
        revision = self.env['clearance.revision'].search(
            [('clearance_id', '=', clearance.id)])
        self.assertEqual(revision.reason, reason)
        message = clearance.message_ids.filtered(
            lambda m: m.message_type == 'comment')
        self.assertEqual(len(message), 1)
        self.assertNotIn('<script>', message.body)
        self.assertIn('&lt;script&gt;', message.body)
        self.assertEqual(message.partner_ids, self.partner_agent)
        # Queued, not sent synchronously
        mails = self.env['mail.mail'].search(
            [('mail_message_id', '=', message.id)])
        self.assertTrue(mails)
        self.assertEqual(set(mails.mapped('state')), {'outgoing'})
