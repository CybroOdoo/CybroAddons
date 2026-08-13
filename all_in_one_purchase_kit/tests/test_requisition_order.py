# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swaraj R (odoo@cybrosys.com)
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
###############################################################################
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

@tagged('post_install', '-at_install')
class TestRequisitionOrder(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Requisition Order Partner'})
        cls.product = cls.env['product.product'].create({
            'name': 'Requisition Order Product',
            'type': 'consu',
        })
        cls.dept = cls.env['hr.department'].create({'name': 'Requisition Dept'})
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Requisition Employee',
            'department_id': cls.dept.id,
        })
        cls.requisition = cls.env['employee.purchase.requisition'].create({
            'employee_id': cls.employee.id,
            'user_id': cls.env.user.id,
        })

    def test_requisition_order_fields_and_computes(self):
        """Test compute description and field assignments on requisition order."""
        req_order = self.env['requisition.order'].create({
            'requisition_product_id': self.requisition.id,
            'product_id': self.product.id,
            'quantity': 15,
            'requisition_type': 'purchase_order',
            'partner_id': self.partner.id,
        })
        
        # Test description computation
        req_order._compute_product_id()
        self.assertIn('Requisition Order Product', req_order.description)
