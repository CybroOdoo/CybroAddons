# -*- coding: utf-8 -*-
"""pos reports"""

import re

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.osv.expression import expression


class PosReport(models.Model):
    """inherited report.pos.order"""
    _inherit = "report.pos.order"

    branch_id = fields.Many2one('res.branch', 'Branch', readonly=True)

    def _select(self):
        """override select methode to add branch"""
        return super(PosReport, self)._select() + ", s.branch_id as branch_id"

    def _group_by(self):
        """override groupby methode"""
        return super(PosReport, self)._group_by() + ", s.branch_id"
