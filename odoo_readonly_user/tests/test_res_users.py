# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: AYANA KP (odoo@cybrosys.com)
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
################################################################################
from odoo.tests import common
from odoo.exceptions import ValidationError

class TestResUsers(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            cls.env.cr.execute("ALTER TABLE res_partner ALTER COLUMN autopost_bills DROP NOT NULL")
        except Exception:
            pass
        try:
            cls.env.cr.execute("ALTER TABLE res_users_settings ALTER COLUMN color_scheme DROP NOT NULL")
        except Exception:
            pass
        cls.readonly_group = cls.env.ref('odoo_readonly_user.group_users_readonly')

    def test_prevent_admin_readonly(self):
        """Test that Admin cannot be assigned to the readonly group."""
        admin_user = self.env.ref('base.user_admin')
        
        # Test assigning admin to readonly group through write
        with self.assertRaises(ValidationError) as cm:
            admin_user.with_user(admin_user).write({
                'group_ids': [(4, self.readonly_group.id)]
            })
            
        self.assertEqual(cm.exception.args[0], "Readonly access denied for Admin")
        
        # Another admin shouldn't be able to assign themselves
        new_admin = self.env['res.users'].create({
            'name': 'New Admin',
            'login': 'new_admin',
            'group_ids': [(4, self.env.ref('base.group_system').id)],
        })
        
        with self.assertRaises(ValidationError) as cm2:
            new_admin.with_user(new_admin).write({
                'group_ids': [(4, self.readonly_group.id)]
            })
            
        self.assertEqual(cm2.exception.args[0], "Readonly access denied for Admin")
        
        # Admin can assign a normal user to readonly group
        normal_user = self.env['res.users'].create({
            'name': 'Normal User',
            'login': 'normal_user',
        })
        
        # This should not raise an exception
        normal_user.with_user(admin_user).write({
            'group_ids': [(4, self.readonly_group.id)]
        })
        self.assertIn(self.readonly_group, normal_user.group_ids)
