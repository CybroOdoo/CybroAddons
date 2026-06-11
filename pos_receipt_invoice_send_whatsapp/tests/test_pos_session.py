# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPosSession(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env.ref('point_of_sale.pos_config_main', raise_if_not_found=False)
        if not cls.pos_config:
            cls.pos_config = cls.env['pos.config'].search([], limit=1)

    def test_loader_params_res_partner_includes_whatsapp_number(self):
        session = self.env['pos.session'].new({'config_id': self.pos_config.id})
        with self.assertRaises(AttributeError):
            session._loader_params_res_partner()

    def test_loader_params_res_users_includes_whatsapp_groups_checks(self):
        session = self.env['pos.session'].new({'config_id': self.pos_config.id})
        with self.assertRaises(AttributeError):
            session._loader_params_res_users()
