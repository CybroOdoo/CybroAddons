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
from odoo.tests import tagged

from .common import PharmaTraceabilityCommon


@tagged('post_install', '-at_install')
class TestAuditTrail(PharmaTraceabilityCommon):
    """The audit trail view over tracked changes."""

    def test_tracked_change_listed(self):
        """A tracked change on a regulated record shows in the audit trail."""
        lot = self.create_lot(name='AUDIT-1')
        field = self.env['ir.model.fields']._get('stock.lot', 'lot_status')
        self.env['mail.message'].create(
            {
                'model': 'stock.lot',
                'res_id': lot.id,
                'message_type': 'notification',
                'tracking_value_ids': [
                    (
                        0,
                        0,
                        {
                            'field_id': field.id,
                            'old_value_char': 'Quarantine',
                            'new_value_char': 'Approved',
                        },
                    )
                ],
            }
        )
        self.env.flush_all()
        entry = self.env['pharma.audit.trail'].search([('model', '=', 'stock.lot'), ('res_id', '=', lot.id)])
        self.assertEqual(
            (entry.record_name, entry.old_value, entry.new_value), ('AUDIT-1', 'Quarantine', 'Approved')
        )
        self.assertEqual(entry.field_name, field.field_description)

    def test_coa_change_listed_after_install(self):
        """CoA changes are in the view built at install, without a rebuild.

        The view is first built before the pharma_coa table exists; the
        post_init_hook rebuilds it so CoAs are included."""
        coa = self.env['pharma.coa'].create({})
        field = self.env['ir.model.fields']._get('pharma.coa', 'released_by')
        self.env['mail.message'].create(
            {
                'model': 'pharma.coa',
                'res_id': coa.id,
                'message_type': 'notification',
                'tracking_value_ids': [(0, 0, {'field_id': field.id, 'new_value_char': 'QA'})],
            }
        )
        self.env.flush_all()
        entry = self.env['pharma.audit.trail'].search([('model', '=', 'pharma.coa'), ('res_id', '=', coa.id)])
        self.assertEqual(entry.record_name, coa.name)

    def test_view_rebuild(self):
        """The view rebuilds when optional tables are missing."""
        Trail = self.env['pharma.audit.trail']
        Trail.init(_excluded_tables=['pharma_coa', 'pharma_sop'])
        Trail.init(
            _excluded_tables=[
                'pharma_bmr',
                'pharma_qc_test_order',
                'pharma_coa',
                'stock_lot',
                'pharma_sop',
                'pharma_deviation',
                'pharma_capa',
            ]
        )
        self.assertFalse(Trail.search([]))
        Trail.init()
