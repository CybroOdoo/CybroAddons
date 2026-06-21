# -*- coding: utf-8 -*-
##############################################################################
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
##############################################################################
from odoo.tests import tagged, TransactionCase
from odoo.addons.http_routing.tests.common import MockRequest


@tagged('post_install', '-at_install')
class TestWebsiteRobots(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env['website'].create({
            'name': 'Test Robots Website',
            'mode': 'custom',
            'robots_txt': 'User-agent: *\nDisallow: /admin',
        })

    def test_wizard_default_mode(self):
        """Test that the default mode of the wizard is retrieved from the website."""
        with MockRequest(self.env, website=self.website):
            wizard = self.env['website.robots'].create({})
            self.assertEqual(wizard.mode, 'custom')

    def test_wizard_onchange_mode(self):
        """Test the wizard's _onchange_mode method for different modes."""
        with MockRequest(self.env, website=self.website):
            # Instantiate the wizard
            wizard = self.env['website.robots'].create({'mode': 'custom'})
            
            # Switch mode to allow_all and trigger onchange
            wizard.mode = 'allow_all'
            wizard._onchange_mode()
            self.assertEqual(wizard.content, "User-agent: *\n            Allow: /")

            # Switch mode to disallow_all and trigger onchange
            wizard.mode = 'disallow_all'
            wizard._onchange_mode()
            self.assertEqual(wizard.content, "User-agent: *\n            Disallow: /")

            # Switch mode to custom and trigger onchange when robots_txt is empty
            self.website.robots_txt = False
            wizard.mode = 'custom'
            wizard._onchange_mode()
            self.assertEqual(wizard.content, " ")

    def test_wizard_action_save(self):
        """Test that the wizard action_save correctly updates the website."""
        with MockRequest(self.env, website=self.website):
            # Case 1: save allow_all
            wizard = self.env['website.robots'].create({
                'mode': 'allow_all',
                'content': "User-agent: *\n            Allow: /"
            })
            wizard.action_save()
            self.assertEqual(self.website.mode, 'allow_all')
            self.assertEqual(self.website.robots_txt, "User-agent: *\n            Allow: /")

            # Case 2: save disallow_all
            wizard = self.env['website.robots'].create({
                'mode': 'disallow_all',
                'content': "User-agent: *\n            Disallow: /"
            })
            wizard.action_save()
            self.assertEqual(self.website.mode, 'disallow_all')
            self.assertEqual(self.website.robots_txt, "User-agent: *\n            Disallow: /")

            # Case 3: save custom
            wizard = self.env['website.robots'].create({
                'mode': 'custom',
                'content': "User-agent: Googlebot\nDisallow: /"
            })
            wizard.action_save()
            self.assertEqual(self.website.mode, 'custom')
            self.assertEqual(self.website.robots_txt, "User-agent: Googlebot\nDisallow: /")
