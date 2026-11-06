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
from lxml import etree

from odoo.tests import tagged

from .common import PharmaTraceabilityCommon


@tagged('post_install', '-at_install')
class TestAccess(PharmaTraceabilityCommon):
    """Each role can open the screens it is given."""

    def read_form(self, record, user, view=None):
        """Read every field of ``record``'s form as ``user``, as the web client does."""
        records = record.with_user(user)
        views = records.get_views([(view and view.id or False, 'form')])
        arch = etree.fromstring(views['views']['form']['arch'])
        fnames = {
            node.get('name')
            for node in arch.iter('field')
            if not any(p.tag in ('list', 'kanban') for p in node.iterancestors())
        }
        return records.read([f for f in fnames if f in record._fields])

    def test_roles_open_forms(self):
        """Operator and QA open the release, the CoA and the batch genealogy.

        The genealogy is a lot form, so it needs Inventory access: it is read
        by a QA reviewer who also holds Inventory rights."""
        release = self.queued_release()
        release.with_user(self.qa_user).action_confirm()
        genealogy = self.env.ref('pharma_traceability_coa.stock_lot_genealogy_form')
        qa_stock = self.qa_user.copy({'login': 'pharma_coa_qa_stock'})
        qa_stock.group_ids = [(4, self.env.ref('stock.group_stock_user').id)]
        for user in (self.operator, self.qa_user):
            self.read_form(release, user)
            self.read_form(release.coa_id, user)
            self.env['pharma.audit.trail'].with_user(user).search([], limit=1)
        for user in (self.operator, qa_stock):
            self.read_form(release.lot_id, user, genealogy)
