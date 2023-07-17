# -*- coding: utf-8 -*-


from odoo import fields, models


class ReportSupportUser(models.Model):
    _inherit = "report.project.task.user"

    is_support_package = fields.Boolean(string='Support Package', readonly=True)

    def _select(self):
        return super(ReportSupportUser, self)._select() + """,
            t.is_support_package"""
