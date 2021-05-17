# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ReportSupportUser(models.Model):
    _inherit = "report.project.task.user"

    is_support_package = fields.Boolean(string='Support Package', readonly=True)

    def _select(self):
        return super(ReportSupportUser, self)._select() + """,
            t.is_support_package"""
