# -*- coding: utf-8 -*-
#############################################################################
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
#############################################################################
from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestLoginDetail(TransactionCase):
    """ Test cases for the model login.detail and its access roles """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.internal_user = new_test_user(
            cls.env, login='login_detail_internal', groups='base.group_user')
        cls.log_user = new_test_user(
            cls.env, login='login_detail_log_user', name='Log User',
            groups='login_user_detail.group_login_detail_user')
        cls.log_manager = new_test_user(
            cls.env, login='login_detail_log_manager', name='Log Manager',
            groups='login_user_detail.group_login_detail_manager')
        cls.own_record = cls.env['login.detail'].create({
            'user_id': cls.log_user.id,
            'name': cls.log_user.name,
            'ip_address': '10.0.0.5',
        })
        cls.other_record = cls.env['login.detail'].create({
            'user_id': cls.log_manager.id,
            'name': cls.log_manager.name,
            'ip_address': '10.0.0.6',
        })
        cls.records = cls.own_record | cls.other_record

    def test_create_login_detail(self):
        """ Test the creation of a login detail record """
        login_record = self.env['login.detail'].create({
            'name': 'Test User',
            'ip_address': '127.0.0.1',
        })
        self.assertEqual(login_record.name, 'Test User')
        self.assertEqual(login_record.ip_address, '127.0.0.1')
        self.assertTrue(login_record.date_time,
                        "Date time should be set by default")
        self.assertLessEqual(login_record.date_time, fields.Datetime.now())

    def test_internal_user_cannot_read_login_details(self):
        """ Internal users without a Login Details role see nothing """
        with self.assertRaises(AccessError):
            self.own_record.with_user(self.internal_user).read(['ip_address'])

    def test_user_role_sees_only_own_logins(self):
        """ The User role reads its own logins and no one else's """
        LoginDetail = self.env['login.detail'].with_user(self.log_user)
        self.assertEqual(
            LoginDetail.search([('id', 'in', self.records.ids)]),
            self.own_record)
        self.assertEqual(
            self.own_record.with_user(self.log_user).ip_address, '10.0.0.5')
        with self.assertRaises(AccessError):
            self.other_record.with_user(self.log_user).read(['ip_address'])

    def test_manager_role_sees_all_logins(self):
        """ The Manager role reads the logins of every user """
        LoginDetail = self.env['login.detail'].with_user(self.log_manager)
        self.assertEqual(
            LoginDetail.search([('id', 'in', self.records.ids)]),
            self.records)

    def test_roles_cannot_change_login_details(self):
        """ Neither role can create, edit or delete audit records """
        for user in (self.log_user, self.log_manager):
            record = self.own_record.with_user(user)
            with self.assertRaises(AccessError):
                record.write({'ip_address': '1.1.1.1'})
            with self.assertRaises(AccessError):
                record.unlink()
            with self.assertRaises(AccessError):
                self.env['login.detail'].with_user(user).create(
                    {'name': 'Fake Login'})

    def test_deleting_user_keeps_login_history(self):
        """ Removing a user keeps their login records for auditing """
        self.log_user.unlink()
        self.assertTrue(self.own_record.exists())
        self.assertFalse(self.own_record.user_id)
        self.assertEqual(self.own_record.name, 'Log User')
