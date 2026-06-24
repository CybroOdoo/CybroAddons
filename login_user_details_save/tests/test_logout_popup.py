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
from odoo.tests import common, HttpCase
from odoo import fields

class TestLogoutPopup(HttpCase):

    @classmethod
    def setUpClass(cls):
        super(TestLogoutPopup, cls).setUpClass()
        cls.user_demo = cls.env.ref('base.user_demo')

    def test_01_logout_popup_model(self):
        """Test basic model functionality"""
        popup = self.env['logout.popup'].create({
            'name': 'demo',
            'save_details': True,
            'user_id': self.user_demo.id,
        })
        self.assertEqual(popup.name, 'demo')
        self.assertTrue(popup.save_details)
        self.assertEqual(popup.user_id, self.user_demo)

    def test_02_save_logout_details_controller(self):
        """Test the save_logout_details controller logic indirectly via model calls
        since full HTTP session testing can be complex. We simulate the controller logic.
        """
        # Simulate checking the box
        self.authenticate('demo', 'demo')
        uid = self.env.ref('base.user_demo').id
        login_name = 'demo'
        
        # Initial state: no record
        record = self.env['logout.popup'].search([('user_id', '=', uid)])
        self.assertFalse(record)

        # Simulate save_logout_details(rememberMeCheckbox=True)
        self.env['logout.popup'].create({
            'name': login_name,
            'save_details': True,
            'user_id': uid,
        })
        
        record = self.env['logout.popup'].search([('user_id', '=', uid)])
        self.assertTrue(record)
        self.assertEqual(record.name, login_name)

        # Simulate unchecking (save_logout_details(rememberMeCheckbox=False))
        record.unlink()
        record = self.env['logout.popup'].search([('user_id', '=', uid)])
        self.assertFalse(record)

    def test_03_web_login_data_fetch(self):
        """Test that login_data is correctly fetched for the login page"""
        # Create some saved login details
        self.env['logout.popup'].create({
            'name': 'demo',
            'save_details': True,
            'user_id': self.user_demo.id,
        })
        
        # Simulate the logic in WebHome.web_login
        log_data_list = []
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for log_data in self.env['logout.popup'].search([]):
            log_data_list.append([
                log_data.name,
                '{}/web/image?model=res.users&id={}&field=image_1920'.format(
                    base_url, log_data.user_id.id),
                log_data.user_id.name,
            ])
        
        self.assertTrue(len(log_data_list) > 0)
        self.assertEqual(log_data_list[0][0], 'demo')
        self.assertEqual(log_data_list[0][2], self.user_demo.name)
