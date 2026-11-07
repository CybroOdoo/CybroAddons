# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import api, fields, models


class PosSession(models.Model):
    """To add analytic tags in pos session"""
    _inherit = 'pos.session'

    pos_analytic_account_id = fields.Many2one('account.analytic.account',
                                              string='Pos Analytic Tag',
                                              help="Pos Analytic account in"
                                                   " pos session",
                                              readonly=True)

    @api.model
    def _load_pos_data_fields(self, config):
        """Add the POS analytic account field to the POS session data."""
        result = super()._load_pos_data_fields(config)
        if 'pos_analytic_account_id' not in result:
            result.append('pos_analytic_account_id')
        return result

    def _create_session_account_move(self, orders):
        """Call the parent class method using super() and creates
         analytic distribution model"""
        res = super()._create_session_account_move(orders)
        self.pos_analytic_account_id = self.config_id.analytic_account_id
        analytic_account = self.pos_analytic_account_id or self.config_id.analytic_account_id
        if analytic_account:
            analytic_dist = {str(analytic_account.id): 100}
            moves = res | self._get_related_account_moves()
            for move in moves:
                for rec in move.line_ids:
                    rec.sudo().write({
                        'analytic_distribution': analytic_dist
                    })
        else:
            moves = res | self._get_related_account_moves()
            for move in moves:
                for rec in move.line_ids:
                    rec.sudo().write({
                        'analytic_distribution': {}
                    })
        return res