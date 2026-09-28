# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:Abhijith CK(odoo@cybrosys.com)
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
from odoo.tests.common import TransactionCase

class TestResConfigSettings(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestResConfigSettings, cls).setUpClass()
        
        # Create Employee to test the check_list_enable propagation
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Config Employee',
        })

    def test_res_config_settings(self):
        # Test settings for enabling checklist
        settings = self.env['res.config.settings'].create({
            'enable_checklist': True,
        })
        settings.set_values()
        
        # Check if parameter is saved
        param = self.env['ir.config_parameter'].sudo().get_param('employee_check_list.enable_checklist')
        self.assertEqual(param, 'True')
        
        # Check if employee field is updated
        self.assertTrue(self.employee.check_list_enable)
