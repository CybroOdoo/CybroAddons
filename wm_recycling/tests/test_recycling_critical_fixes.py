#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install', 'wm_recycling')
class TestRecyclingCriticalFixes(TransactionCase):
    """Regression test: recyclers without Sales rights can open recycling orders."""

    def test_recycler_without_sales_rights_reads_order(self):
        recycler = new_test_user(self.env, login='wm_fix_recycler', groups='wm_base.group_wm_recycler')
        self.assertFalse(recycler.has_group('sales_team.group_sale_salesman'))
        product = self.env['product.product'].create({'name': 'Fix PET', 'is_waste_material': True})
        batch = self.env['waste.batch'].create({'line_ids': [(0, 0, {'product_id': product.id, 'quantity': 10.0})]})
        order = self.env['recycling.order'].create({'waste_batch_id': batch.id})
        self.env['sale.order'].create({'partner_id': self.env.user.partner_id.id, 'origin': order.name})

        order_as_recycler = order.with_user(recycler)
        order_as_recycler.invalidate_recordset()
        self.assertEqual(order_as_recycler.sale_order_count, 1)
