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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

@tagged('post_install', '-at_install')
class TestPosPaymentMethod(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.payment_method = cls.env['pos.payment.method'].create({
            'name': 'Hotel Charge Test',
            'is_hotel_charge': True,
        })

    def test_load_pos_data_fields(self):
        """Test hotel charge field loading."""
        fields_list = self.payment_method._load_pos_data_fields(False)
        self.assertIn('is_hotel_charge', fields_list)

    def test_is_write_forbidden(self):
        """Test write is not forbidden with install_mode in context."""
        result = self.payment_method.with_context(install_mode=True)._is_write_forbidden({'name'})
        self.assertFalse(result)
