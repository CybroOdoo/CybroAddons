# -*- coding: utf-8 -*-
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
from datetime import date, datetime

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .common import PharmaCapaCommon


@tagged('post_install', '-at_install')
class TestDeviation(PharmaCapaCommon):
    """Deviation numbering, investigation and closure."""

    def test_numbering_and_deadline(self):
        """Deviations are numbered permanently; the deadline follows severity."""
        deviation = self.create_deviation(classification='critical')
        self.assertNotEqual(deviation.name, 'New')
        self.assertEqual(deviation.raised_by, self.operator)
        deviation.sudo().write({'raised_on': datetime(2026, 1, 1, 9, 0)})
        self.assertEqual(deviation.deadline_date, date(2026, 1, 4))
        deviation.classification = 'minor'
        self.assertEqual(deviation.deadline_date, date(2026, 1, 15))
        with self.assertRaises(UserError):
            deviation.name = 'DEV-X'
        deviation.sudo().raised_on = False
        self.assertFalse(deviation.deadline_date)

    def test_investigate_raises_capa(self):
        """QA starts the investigation; a corrective CAPA is raised once."""
        deviation = self.create_deviation()
        with self.assertRaises(UserError):
            deviation.with_user(self.operator).action_investigate()
        deviation.with_user(self.qa_only).action_investigate()
        self.assertEqual(deviation.status, 'under_investigation')
        capa = deviation.capa_ids
        self.assertEqual((capa.capa_type, capa.assigned_to, capa.due_date),
                         ('corrective', self.qa_only, deviation.deadline_date))
        self.assertEqual((deviation.capa_count, deviation.preventive_capa_count), (1, 0))
        self.assertFalse(deviation.all_capas_closed)
        with self.assertRaises(UserError):
            deviation.with_user(self.qa_only).action_investigate()

    def test_close_checks(self):
        """Closing needs QA, a disposition and every CAPA closed."""
        deviation = self.create_deviation()
        with self.assertRaises(UserError):
            deviation.with_user(self.qa_only).action_close()
        deviation.with_user(self.qa_only).action_investigate()
        with self.assertRaises(UserError):
            deviation.with_user(self.operator).action_close()
        with self.assertRaises(UserError):
            deviation.with_user(self.qa_only).action_close()
        deviation.with_user(self.qa_only).disposition = 'release'
        with self.assertRaises(UserError):
            deviation.with_user(self.qa_only).action_close()
        self.close_capa(deviation.capa_ids)
        self.assertTrue(deviation.all_capas_closed)
        deviation.with_user(self.qa_only).action_close()
        self.assertEqual(deviation.status, 'closed')

    def test_close_without_capa(self):
        """A deviation with no CAPA cannot close."""
        deviation = self.create_deviation()
        deviation.sudo().write({'status': 'under_investigation', 'disposition': 'release'})
        with self.assertRaises(UserError):
            deviation.with_user(self.qa_only).action_close()

    def test_reject_segregates_lot(self):
        """A rejected deviation rejects its lot and reports the missing location."""
        lot = self.create_lot(name='DEV-LOT')
        deviation = self.investigated(lot_id=lot.id)
        self.env.company.pharma_rejected_location_id = False
        self.close_capa(deviation.capa_ids)
        deviation.with_user(self.qa_only).disposition = 'reject'
        deviation.with_user(self.qa_only).action_close()
        self.assertEqual(lot.lot_status, 'rejected')
        self.assertTrue(any('no Rejected Location' in m.body for m in deviation.message_ids))

    def test_reject_moves_stock(self):
        """With a Rejected location and stock on hand, the lot is moved there."""
        lot = self.create_lot(name='DEV-STOCK')
        warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.company.id)], limit=1)
        rejected = self.env['stock.location'].create({
            'name': 'Rejected', 'usage': 'internal', 'location_id': warehouse.view_location_id.id,
        })
        self.env.company.pharma_rejected_location_id = rejected
        self.env['stock.quant']._update_available_quantity(
            self.product, warehouse.lot_stock_id, 5.0, lot_id=lot)
        deviation = self.investigated(lot_id=lot.id)
        self.close_capa(deviation.capa_ids)
        deviation.with_user(self.qa_only).disposition = 'reject'
        deviation.with_user(self.qa_only).action_close()
        self.assertTrue(any('moved to the Rejected location' in m.body for m in deviation.message_ids))

    def test_access(self):
        """Pharma users read deviations; nobody but the administrator deletes them."""
        deviation = self.create_deviation()
        with self.assertRaises(AccessError):
            deviation.with_user(self.qa_only).check_access('unlink')
        with self.assertRaises(AccessError):
            self.env['pharma.deviation'].with_user(self.qa_only).check_access('create')
