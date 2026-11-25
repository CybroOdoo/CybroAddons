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
#############################################################################
from datetime import datetime, timedelta
from odoo import Command
from odoo.tests.common import HttpCase, new_test_user, tagged


@tagged('post_install', '-at_install', 'pet_shop_management')
class TestPetShopPortal(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.portal_user = new_test_user(
            cls.env,
            name='Portal Pet Owner',
            login='portal_pet_owner',
            email='portal_pet_owner@example.com',
            groups='base.group_portal',
        )
        cls.other_user = new_test_user(
            cls.env,
            name='Other Portal User',
            login='other_portal_user',
            email='other_user@example.com',
            groups='base.group_portal',
        )
        cls.internal_user = new_test_user(
            cls.env,
            name='Internal User',
            login='internal_pet_user',
            email='internal_user@example.com',
            groups='base.group_user,pet_shop_management.pet_shop_management_group_pet_user,sales_team.group_sale_salesman_all_leads',
        )
        cls.partner = cls.portal_user.partner_id
        cls.other_partner = cls.other_user.partner_id

        # Pet for portal user
        cls.pet = cls.env['product.product'].create({
            'name': 'Milo',
            'is_pet': True,
            'customer_id': cls.partner.id,
            'partner_id': cls.partner.id,
        })

        # Pet for other user
        cls.other_pet = cls.env['product.product'].create({
            'name': 'Other Dog',
            'is_pet': True,
            'customer_id': cls.other_partner.id,
            'partner_id': cls.other_partner.id,
        })

        # Sitting schedule for portal user
        cls.schedule = cls.env['sitting.schedule'].create({
            'name': 'Milo Schedule',
            'date_start': datetime.now() + timedelta(days=2),
            'end_date': datetime.now() + timedelta(days=2, hours=3),
            'pet_info_ids': [Command.create({
                'num': cls.pet.id,
                'customer': cls.partner.id,
            })],
        })

    def test_01_portal_home_and_counters(self):
        """ Test portal home and JSON-RPC counters """
        self.authenticate('portal_pet_owner', 'portal_pet_owner')

        res = self.url_open('/my')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'/my/pets', res.content)
        self.assertIn(b'/my/sittings', res.content)

        # Test counters
        counters_res = self.make_jsonrpc_request(
            '/my/counters',
            {
                'counters': {
                    'pets_count': 'client_category',
                    'sittings_count': 'client_category',
                }
            }
        )
        self.assertEqual(counters_res.get('pets_count'), 1)
        self.assertEqual(counters_res.get('sittings_count'), 1)

    def test_02_portal_my_pets_list_and_detail(self):
        """ Test pet list and detail access control """
        # 1. Unauthenticated access redirects to login
        self.authenticate(None, None)
        unauth_res = self.url_open(
            f'/my/pets/{self.pet.id}', allow_redirects=False
        )
        self.assertIn(unauth_res.status_code, (302, 303))
        self.assertIn('/web/login', unauth_res.headers.get('Location', ''))

        # 2. Authenticated portal owner
        self.authenticate('portal_pet_owner', 'portal_pet_owner')

        # List view
        res = self.url_open('/my/pets')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Milo', res.content)
        self.assertNotIn(b'Other Dog', res.content)

        # Detail view for own pet
        detail_res = self.url_open(f'/my/pets/{self.pet.id}')
        self.assertEqual(detail_res.status_code, 200)
        self.assertIn(b'Milo', detail_res.content)

        # Accessing other user's pet returns 302/303 redirecting to /my
        forbidden_res = self.url_open(
            f'/my/pets/{self.other_pet.id}', allow_redirects=False
        )
        self.assertIn(forbidden_res.status_code, (302, 303))
        self.assertTrue(
            forbidden_res.headers.get('Location', '').endswith('/my')
        )

        # Followed redirect lands on /my without other pet content
        forbidden_landing = self.url_open(f'/my/pets/{self.other_pet.id}')
        self.assertEqual(forbidden_landing.status_code, 200)
        self.assertNotIn(b'Other Dog', forbidden_landing.content)

    def test_03_portal_pet_pdf_download(self):
        """ Test downloading pet information report from portal """
        self.authenticate('portal_pet_owner', 'portal_pet_owner')

        res = self.url_open(f'/my/pets/{self.pet.id}?report_type=html')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Milo', res.content)

    def test_04_portal_my_sittings(self):
        """ Test sittings portal list and single breadcrumb assertion """
        self.authenticate('portal_pet_owner', 'portal_pet_owner')

        res = self.url_open('/my/sittings')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Milo', res.content)
        self.assertIn(b'Pet Sitting Schedules', res.content)
        self.assertEqual(
            res.content.count(b'class="breadcrumb-item active"'), 1
        )

        self.authenticate('internal_pet_user', 'internal_pet_user')
        res_internal = self.url_open('/my/sittings')
        self.assertEqual(res_internal.status_code, 200)
        self.assertIn(b'Pet Sitting Schedules', res_internal.content)
        self.assertEqual(
            res_internal.content.count(b'class="breadcrumb-item active"'), 1
        )

    def test_05_portal_coverage_and_edge_cases(self):
        """ Test edge cases and helper methods in portal controllers """
        from ..controllers.pet_shop_management import PortalPets
        from ..controllers.portal import PortalSittingsSchedules

        # Test non-existent pet redirect (assert HTTP 302/303 to /my)
        self.authenticate('portal_pet_owner', 'portal_pet_owner')
        invalid_pet_res = self.url_open(
            '/my/pets/99999999', allow_redirects=False
        )
        self.assertIn(invalid_pet_res.status_code, (302, 303))
        self.assertTrue(
            invalid_pet_res.headers.get('Location', '').endswith('/my')
        )

        # Test internal user domain retrieval
        self.authenticate('internal_pet_user', 'internal_pet_user')
        admin_pets_res = self.url_open('/my/pets')
        self.assertEqual(admin_pets_res.status_code, 200)

        # Test controller helper methods
        pets_ctrl = PortalPets()
        sittings_ctrl = PortalSittingsSchedules()

        # Unrelated counter delegation to super
        self.assertEqual(
            pets_ctrl._prepare_portal_counter_values('unrelated_counter'),
            (False, False, False)
        )
        self.assertEqual(
            sittings_ctrl._prepare_portal_counter_values('unrelated_counter'),
            (False, False, False)
        )
