# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana J(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import fields, models


class PosReport(models.Model):
    """inherited report.pos.order"""
    _inherit = "report.pos.order"

    branch_id = fields.Many2one('res.branch', string='Branch',
                                help='Allowed Branches', readonly=True)

    def _select(self):
        """override select method to add branch"""
        return super(PosReport, self)._select() + ", s.branch_id as branch_id"

    def _group_by(self):
        """override group by method"""
        return super(PosReport, self)._group_by() + ", s.branch_id"
