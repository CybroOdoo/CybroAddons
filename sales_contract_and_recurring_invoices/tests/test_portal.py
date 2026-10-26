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
from odoo import fields
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestSubscriptionPortal(common.HttpCase):
    """ Test suite for Subscription Contracts Customer Portal and Security Access """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.portal_user = cls.env['res.users'].create({
            'name': 'Test Portal Client',
            'login': 'client_portal_user',
            'password': 'client_portal_user',
            'email': 'client_portal@example.com',
            'group_ids': [fields.Command.set([cls.env.ref('base.group_portal').id])],
        })

        cls.other_portal_user = cls.env['res.users'].create({
            'name': 'Other Portal Client',
            'login': 'other_portal_user',
            'password': 'other_portal_user',
            'email': 'other_portal@example.com',
            'group_ids': [fields.Command.set([cls.env.ref('base.group_portal').id])],
        })

        cls.contract = cls.env['subscription.contracts'].create({
            'name': 'Portal Security Contract',
            'partner_id': cls.portal_user.partner_id.id,
            'state': 'ongoing',
            'date_start': fields.Date.today(),
            'recurring_period': 6,
            'recurring_period_interval': 'months',
        })

    def test_01_portal_my_contracts_list(self):
        """ Test /my/contracts and /my/contracts/page/1 for authenticated portal client """
        self.authenticate('client_portal_user', 'client_portal_user')
        res = self.url_open('/my/contracts')
        self.assertEqual(res.status_code, 200)
        self.assertIn('Portal Security Contract', res.text)

        # Test pagination route
        res_page = self.url_open('/my/contracts/page/1')
        self.assertEqual(res_page.status_code, 200)
        self.assertIn('Portal Security Contract', res_page.text)

    def test_02_portal_contract_detail_access_control(self):
        """ Test /contracts/<id> detail view allows owner and denies unauthorized user """
        # Authorized owner
        self.authenticate('client_portal_user', 'client_portal_user')
        res_owner = self.url_open(f'/contracts/{self.contract.id}')
        self.assertEqual(res_owner.status_code, 200)
        self.assertIn('Portal Security Contract', res_owner.text)

        # Unauthorized portal user
        self.authenticate('other_portal_user', 'other_portal_user')
        res_other = self.url_open(f'/contracts/{self.contract.id}')
        self.assertIn(res_other.status_code, (403, 404))

    def test_03_portal_pdf_report_download(self):
        """ Test /my/contracts/report/<id> downloads PDF for authorized user and blocks unauthorized """
        # Authorized owner
        self.authenticate('client_portal_user', 'client_portal_user')
        res = self.url_open(f'/my/contracts/report/{self.contract.id}')
        self.assertEqual(res.status_code, 200)
        self.assertIn('application/pdf', res.headers.get('Content-Type', ''))

        # Unauthorized portal user
        self.authenticate('other_portal_user', 'other_portal_user')
        res_unauth = self.url_open(f'/my/contracts/report/{self.contract.id}')
        self.assertIn(res_unauth.status_code, (403, 404))
