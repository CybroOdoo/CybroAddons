# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies(odoo@cybrosys.com)
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
###############################################################################
from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError

class TestRestrictPricelistUser(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = cls.env['res.users'].create({
            'name': 'Test User',
            'login': 'test_user_pricelist',
            'email': 'test@example.com',
            'groups_id': [(6, 0, [cls.env.ref('sales_team.group_sale_salesman').id])],
        })

        cls.pricelist_1 = cls.env['product.pricelist'].create({
            'name': 'Test Pricelist 1',
        })
        cls.pricelist_2 = cls.env['product.pricelist'].create({
            'name': 'Test Pricelist 2',
        })
        cls.pricelist_3 = cls.env['product.pricelist'].create({
            'name': 'Test Pricelist 3',
        })

    def test_01_pricelist_unrestricted(self):
        """ Test when 'is_restricted' config param is False """
        self.env['ir.config_parameter'].sudo().set_param('restrict_pricelist_user.is_restricted', False)

        # User has no pricelists set
        self.user.pricelist_ids = [(5, 0, 0)]

        pricelists = self.env['product.pricelist'].with_user(self.user).search([])
        
        self.assertIn(self.pricelist_1, pricelists, "User should see all pricelists when unrestricted")
        self.assertIn(self.pricelist_2, pricelists, "User should see all pricelists when unrestricted")
        self.assertIn(self.pricelist_3, pricelists, "User should see all pricelists when unrestricted")

        # Even if user has some pricelists set, if config is False, they should see all
        self.user.pricelist_ids = [(6, 0, [self.pricelist_1.id])]
        pricelists_with_set = self.env['product.pricelist'].with_user(self.user).search([])
        self.assertIn(self.pricelist_2, pricelists_with_set, "User should see all pricelists when config unrestricted, despite having pricelist_ids")

    def test_02_pricelist_restricted_no_user_pricelists(self):
        """ Test when 'is_restricted' is True but user has no pricelists assigned """
        self.env['ir.config_parameter'].sudo().set_param('restrict_pricelist_user.is_restricted', True)
        
        self.user.pricelist_ids = [(5, 0, 0)]
        
        pricelists = self.env['product.pricelist'].with_user(self.user).search([])
        
        self.assertIn(self.pricelist_1, pricelists, "User should see all pricelists if they have no specific pricelists assigned, despite restriction on config")
        self.assertIn(self.pricelist_2, pricelists, "User should see all pricelists if they have no specific pricelists assigned, despite restriction on config")

    def test_03_pricelist_restricted_with_user_pricelists(self):
        """ Test when 'is_restricted' is True and user has pricelists assigned """
        self.env['ir.config_parameter'].sudo().set_param('restrict_pricelist_user.is_restricted', True)
        
        self.user.pricelist_ids = [(6, 0, [self.pricelist_1.id, self.pricelist_2.id])]
        
        pricelists = self.env['product.pricelist'].with_user(self.user).search([])
        
        self.assertIn(self.pricelist_1, pricelists, "User should see assigned pricelists")
        self.assertIn(self.pricelist_2, pricelists, "User should see assigned pricelists")
        self.assertNotIn(self.pricelist_3, pricelists, "User should NOT see unassigned pricelists")

    def test_04_compute_is_restricted_field(self):
        """ Test the compute field is_restricted on res.users """
        self.env['ir.config_parameter'].sudo().set_param('restrict_pricelist_user.is_restricted', True)
        
        # We need to invalidate cache to ensure compute method triggers
        self.env.invalidate_all()
        
        # trigger compute by reading
        self.assertTrue(self.user.is_restricted, "is_restricted should be True on user when config is True")
        
        self.env['ir.config_parameter'].sudo().set_param('restrict_pricelist_user.is_restricted', False)
        
        # We need to invalidate cache to ensure compute method triggers again
        self.env.invalidate_all()
        
        self.assertFalse(self.user.is_restricted, "is_restricted should be False on user when config is False")
