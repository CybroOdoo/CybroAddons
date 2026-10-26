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
from datetime import date

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'wm_collection')
class TestContainerCoverage(TransactionCase):
    """Coverage for wm.container helpers that do not need accounting."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ctype = cls.env['wm.container.type'].create({'name': 'Cov Bin', 'default_tare_weight': 10.0})
        cls.partner = cls.env['res.partner'].create({'name': 'Cov Container Client'})
        cls.point = cls.env['wm.collection.point'].create({'name': 'Cov Bin Site', 'partner_id': cls.partner.id})

    def _container(self, **kw):
        vals = {'name': 'COV-TAG-%s' % self.env['wm.container'].search_count([]),
                'container_type_id': self.ctype.id}
        vals.update(kw)
        return self.env['wm.container'].create(vals)

    def test_rental_full_periods(self):
        c = self._container(rental_period='daily')
        self.assertEqual(c._rental_full_periods(date(2026, 1, 1), date(2026, 1, 11)), (10, date(2026, 1, 11)))
        c.rental_period = 'weekly'
        self.assertEqual(c._rental_full_periods(date(2026, 1, 1), date(2026, 1, 25)), (3, date(2026, 1, 22)))
        c.rental_period = 'monthly'
        self.assertEqual(c._rental_full_periods(date(2026, 1, 15), date(2026, 4, 14)), (2, date(2026, 3, 15)))
        self.assertEqual(c._rental_full_periods(date(2026, 1, 15), date(2026, 4, 15)), (3, date(2026, 4, 15)))
        c.rental_period = 'flat'
        self.assertEqual(c._rental_full_periods(date(2026, 1, 1), date(2026, 6, 1)), (0, date(2026, 1, 1)))
        # end before/equal start or missing dates
        self.assertEqual(c._rental_full_periods(date(2026, 1, 1), date(2026, 1, 1)), (0, date(2026, 1, 1)))
        self.assertEqual(c._rental_full_periods(False, date(2026, 1, 1)), (0, False))

    def test_onchange_collection_point(self):
        c = self.env['wm.container'].new({'name': 'X', 'container_type_id': self.ctype.id})
        c.collection_point_id = self.point
        c._onchange_collection_point_id()
        self.assertEqual(c.status, 'deployed')
        self.assertTrue(c.deployed_date)
        c.collection_point_id = False
        c._onchange_collection_point_id()
        self.assertEqual(c.status, 'in_yard')
        self.assertFalse(c.deployed_date)
        # a damaged container keeps its status when deployed
        c.status = 'damaged'
        c.collection_point_id = self.point
        c._onchange_collection_point_id()
        self.assertEqual(c.status, 'damaged')

    def test_rental_invoice_guards(self):
        c = self._container()
        with self.assertRaises(UserError):
            c.action_create_rental_invoice()  # not deployed
        c.collection_point_id = self.point
        c.rental_rate = 0.0
        with self.assertRaises(UserError):
            c.action_create_rental_invoice()  # free of charge
        c.write({'rental_rate': 10.0, 'rental_period': 'monthly', 'deployed_date': date.today()})
        with self.assertRaises(UserError):
            c.action_create_rental_invoice()  # no full period yet

    def test_counts_and_view_actions(self):
        c = self._container()
        self.assertEqual(self.ctype.unit_count, 1)
        self.assertEqual(c.invoice_count, 0)
        self.assertEqual(c.lift_count, 0)
        self.assertIsNone(c.action_view_invoices())
        self.assertEqual(c.action_view_batches()['domain'], [('container_id', '=', c.id)])
        self.assertEqual(self.ctype.action_view_individual_containers()['domain'],
                         [('container_type_id', '=', self.ctype.id)])
        category = self.env['wm.waste.category'].create({'name': 'Cov Cont Cat', 'code': 'COVC'})
        self.env['waste.batch'].create({'category_id': category.id, 'container_id': c.id})
        self.assertEqual(c.lift_count, 1)

    def test_barcode_unique_per_company(self):
        c = self._container(name='COV-UNIQ')
        with self.assertRaises(Exception):
            self._container(name='COV-UNIQ')
        self.assertTrue(c)
