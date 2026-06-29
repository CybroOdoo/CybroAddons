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
from odoo.exceptions import AccessError
from odoo.fields import Domain

class TestIrRule(common.TransactionCase):
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
        cls.test_user = cls.env['res.users'].create({
            'name': 'Test Readonly User',
            'login': 'test_readonly_user_2',
            'group_ids': [(4, cls.readonly_group.id), (4, cls.env.ref('base.group_user').id)],
        })

    def test_ir_rule_compute_domain(self):
        """Test _compute_domain behavior for readonly user."""
        IrRule = self.env['ir.rule'].with_user(self.test_user)
        
        # Read mode should return the normal domain, meaning no Domain.FALSE
        domain_read = IrRule._compute_domain('res.partner', 'read')
        self.assertNotIn((0, '=', 1), domain_read)
        
        # Write/Create/Unlink mode should return domain ANDed with FALSE for restricted models
        domain_write = IrRule._compute_domain('res.partner', 'write')
        domain_create = IrRule._compute_domain('res.partner', 'create')
        domain_unlink = IrRule._compute_domain('res.partner', 'unlink')
        
        self.assertIn((0, '=', 1), domain_write)
        self.assertIn((0, '=', 1), domain_create)
        self.assertIn((0, '=', 1), domain_unlink)
        
        # Allowed models should not have FALSE appended
        # 'res.users.log' is in the allowed models
        domain_write_allowed = IrRule._compute_domain('res.users.log', 'write')
        self.assertNotIn((0, '=', 1), domain_write_allowed)
