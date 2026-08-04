# -*- coding: utf-8 -*-
##############################################################################
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
##############################################################################
from odoo.tests.common import HttpCase

class TestPetControllers(HttpCase):

    def setUp(self):
        super(TestPetControllers, self).setUp()
        self.user_internal = self.env['res.users'].create({
            'name': 'Internal User',
            'login': 'internal_user',
            'password': 'internal_user',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]
        })
        self.pet = self.env['product.product'].create({
            'name': 'Portal Pet',
            'is_pet': True,
            'responsible_id': self.user_internal.id,
        })

    def test_01_portal_my_pets(self):
        """ Test /my/pets route """
        self.authenticate('internal_user', 'internal_user')
        response = self.url_open('/my/pets')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Portal Pet', response.content)

    def test_02_portal_my_pets_detail(self):
        """ Test /my/pets/<id> route """
        self.authenticate('internal_user', 'internal_user')
        response = self.url_open('/my/pets/%s' % self.pet.id)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Portal Pet', response.content)

    def test_03_portal_my_sittings(self):
        """ Test /my/sittings route """
        self.authenticate('internal_user', 'internal_user')
        response = self.url_open('/my/sittings')
        self.assertEqual(response.status_code, 200)
