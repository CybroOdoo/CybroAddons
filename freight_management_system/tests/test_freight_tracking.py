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
from odoo.tools import mute_logger

from .common import FreightCommon


@tagged('post_install', '-at_install')
class TestFreightTracking(FreightCommon):

    def _wizard(self, env=None, **kwargs):
        order = self._create_order(env=env)
        vals = {
            'freight_id': order.id,
            'source_loc_id': self.port_loading.id,
            'destination_loc_id': self.port_discharging.id,
            'transport_type': 'water',
            'type': 'received',
        }
        vals.update(kwargs)
        return order, (env or self.env)['freight.order.track'].create(vals)

    def test_01_tracking_submission(self):
        """Test tracking submission, record creation and notification"""
        order, wizard = self._wizard()
        wizard.action_order_submit()
        track = self.env['freight.track'].search(
            [('freight_id', '=', order.id)])
        self.assertEqual(track.type, 'received')
        self.assertEqual(track.source_loc_id, self.port_loading)
        self.assertEqual(track.destination_loc_id, self.port_discharging)
        message = order.message_ids.filtered(
            lambda m: m.message_type == 'comment')
        self.assertEqual(len(message), 1)
        # The label is shown, not the selection key
        self.assertIn('Received', message.body)
        self.assertNotIn('received', message.body)
        self.assertIn('Discharging Port', message.body)
        self.assertEqual(message.partner_ids,
                         self.partner_shipper | self.partner_agent)
        mails = self.env['mail.mail'].search(
            [('mail_message_id', '=', message.id)])
        self.assertTrue(mails)
        self.assertEqual(set(mails.mapped('state')), {'outgoing'})

    def test_02_tracking_required_and_escaping(self):
        """The type is required and the names are escaped"""
        with self.assertRaises(Exception), mute_logger('odoo.sql_db'):
            self._wizard(type=False)
        self.port_discharging.name = '<b>Evil</b>'
        order, wizard = self._wizard()
        wizard.action_order_submit()
        message = order.message_ids.filtered(
            lambda m: m.message_type == 'comment')
        self.assertNotIn('<b>', message.body)

    def test_03_freight_user(self):
        """A freight user can track an order"""
        user_env = self.env(user=self.freight_user)
        order, wizard = self._wizard(env=user_env)
        wizard.action_order_submit()
        self.assertEqual(len(order.track_ids), 1)
        with self.assertRaises(ValidationError):
            order.action_confirm()
