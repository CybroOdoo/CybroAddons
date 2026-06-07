# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestResPartner(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.agent_partner = cls.env['res.partner'].create({
            'name': 'Agent Partner',
            'email': 'agent.partner@example.com',
            'is_agent': True,
        })
        cls.customer_partner = cls.env['res.partner'].create({
            'name': 'Customer Partner',
            'email': 'customer.partner@example.com',
            'agent_id': cls.agent_partner.id,
        })
        cls.other_customer_partner = cls.env['res.partner'].create({
            'name': 'Other Customer Partner',
            'email': 'other.customer.partner@example.com',
            'agent_id': cls.agent_partner.id,
        })

    def test_onchange_agent_clears_customer_links_when_partner_is_no_longer_agent(self):
        self.assertEqual(self.customer_partner.agent_id, self.agent_partner)
        self.assertEqual(self.other_customer_partner.agent_id, self.agent_partner)

        self.agent_partner.is_agent = False
        self.agent_partner._onchange_agent()
        self.customer_partner.invalidate_recordset(['agent_id'])
        self.other_customer_partner.invalidate_recordset(['agent_id'])

        self.assertFalse(self.agent_partner.agent_id)
        self.assertFalse(self.customer_partner.agent_id)
        self.assertFalse(self.other_customer_partner.agent_id)
