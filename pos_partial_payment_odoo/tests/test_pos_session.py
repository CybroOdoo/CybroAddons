# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (odoo@cybrosys.info)
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
from unittest.mock import patch

from odoo.addons.point_of_sale.models.pos_session import PosSession as BasePosSession
from odoo.tests import TransactionCase


class TestPosSession(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.payment_method = cls.env['pos.payment.method'].create({
            'name': 'Test Pay Later',
            'company_id': cls.env.company.id,
        })
        cls.config = cls.env['pos.config'].create({
            'name': 'Partial Payment Test Config',
            'company_id': cls.env.company.id,
            'partial_payment': True,
            'payment_method_ids': [(6, 0, cls.payment_method.ids)],
        })

    def setUp(self):
        super().setUp()
        self.config = self.__class__.config

    def open_new_session(self):
        session = self.config.current_session_id
        if not session:
            session = self.env['pos.session'].create({
                'config_id': self.config.id,
                'user_id': self.env.uid,
                'state': 'opened',
            })
        elif session.state != 'opened':
            session.write({'state': 'opened'})
        return session

    def test_loader_params_res_partner_includes_prevent_partial_payment(self):
        session = self.open_new_session()

        with patch.object(
            BasePosSession,
            '_loader_params_res_partner',
            return_value={'search_params': {'fields': ['name']}},
            create=True,
        ):
            params = session._loader_params_res_partner()

        self.assertIn(
            'prevent_partial_payment',
            params['search_params']['fields'],
        )
