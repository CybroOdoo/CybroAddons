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
from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestRecyclingDecisions(TransactionCase):
    """Decision 8: process loss goes to a dedicated per-company
    "Recycling Process Loss" inventory-loss location, created on demand."""

    NAME = 'Recycling Process Loss'

    def _loss_locations(self, company):
        return self.env['stock.location'].with_context(active_test=False).search([
            ('name', '=', self.NAME), ('company_id', '=', company.id)])

    def test_location_created_lazily_and_reused(self):
        company = self.env['res.company'].create({'name': 'Recycling Lazy Co'})
        self.assertFalse(self._loss_locations(company))
        order = self.env['recycling.order'].new({'company_id': company.id})
        loc = order._get_scrap_location()
        self.assertEqual(loc.name, self.NAME)
        self.assertEqual(loc.usage, 'inventory')
        self.assertEqual(loc.company_id, company)
        # Same placement as the company's standard Scrap location
        scrap = self.env['stock.location'].search([
            ('name', '=', 'Scrap'), ('usage', '=', 'inventory'),
            ('company_id', '=', company.id)], limit=1)
        if scrap:
            self.assertEqual(loc.location_id, scrap.location_id)
            self.assertNotEqual(loc, scrap)
        inventory_loss = self.env['ir.default'].sudo()._get(
            'product.template', 'property_stock_inventory', company_id=company.id)
        self.assertNotEqual(loc.id, inventory_loss)
        # Idempotent: no duplicate on the next call
        self.assertEqual(order._get_scrap_location(), loc)
        self.assertEqual(len(self._loss_locations(company)), 1)

    def test_location_is_per_company(self):
        company_2 = self.env['res.company'].create({'name': 'Recycling Decision Co'})
        loc_1 = self.env['recycling.order'].new(
            {'company_id': self.env.company.id})._get_scrap_location()
        loc_2 = self.env['recycling.order'].new(
            {'company_id': company_2.id})._get_scrap_location()
        self.assertNotEqual(loc_1, loc_2)
        self.assertEqual(loc_2.company_id, company_2)
        self.assertEqual(loc_2.name, self.NAME)

    def test_archived_location_is_reactivated(self):
        order = self.env['recycling.order'].new({'company_id': self.env.company.id})
        loc = order._get_scrap_location()
        loc.active = False
        self.assertEqual(order._get_scrap_location(), loc)
        self.assertTrue(loc.active)

    def test_recycler_without_stock_rights_gets_location(self):
        user = new_test_user(self.env, login='rec_decision_user',
                             groups='base.group_user,wm_base.group_wm_recycler')
        company = self.env['res.company'].create({'name': 'Recycling Rights Co'})
        order = self.env['recycling.order'].with_user(user).new(
            {'company_id': company.id})
        loc = order._get_scrap_location()
        self.assertTrue(loc.id)
        self.assertEqual(self._loss_locations(company), loc.sudo())
