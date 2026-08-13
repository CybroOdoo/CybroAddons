# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (https://www.cybrosys.com)
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
################################################################################
from odoo.tests.common import HttpCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestPortalDashboard(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Portal Partner 2',
        })
        cls.user = cls.env['res.users'].create({
            'name': 'Test Portal User 2',
            'login': 'portal_user_test_2',
            'password': 'portal_user_test_2',
            'groups_id': [(6, 0, [cls.env.ref('base.group_portal').id])],
            'partner_id': cls.partner.id,
        })

    def test_portal_home_route(self):
        """Test the /my/home route to ensure the portal dashboard loads."""
        self.authenticate('portal_user_test_2', 'portal_user_test_2')
        response = self.url_open('/my/home')
        self.assertEqual(response.status_code, 200, 'Portal dashboard should load successfully.')
