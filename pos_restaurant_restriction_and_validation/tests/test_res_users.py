# -*- coding: utf-8 -*-
from odoo.tests import tagged
from odoo.tests.common import new_test_user
from odoo.addons.point_of_sale.tests.common import TestPoSCommon


@tagged('post_install', '-at_install')
class TestResUsersRestriction(TestPoSCommon):

    def test_user_pos_security_pin_is_stored(self):
        user = new_test_user(
            self.env,
            login='pos_pin_user',
            groups='base.group_user',
            name='POS PIN User',
            pos_security_pin='1357',
        )

        self.assertEqual(user.pos_security_pin, '1357')

    def test_user_pos_security_pin_field_metadata(self):
        field = self.env['res.users']._fields['pos_security_pin']

        self.assertEqual(field.type, 'char')
        self.assertEqual(field.string, 'POS Security PIN')
