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
from odoo import fields, models, tools
from odoo.tools import SQL
from odoo.tools.sql import table_exists


class PharmaAuditTrail(models.Model):
    """Read-only audit trail of changes across the regulated pharma models."""

    _name = 'pharma.audit.trail'
    _description = 'Audit Trail'
    _auto = False
    _order = 'changed_on desc'

    changed_on = fields.Datetime(
        readonly=True,
        help='Date and time of the change.',
    )
    model_id = fields.Many2one(
        comodel_name='ir.model',
        string='Model Name',
        readonly=True,
        help='Model of the changed record.',
    )
    model = fields.Char(
        related='model_id.model',
        string='Model Technical Name',
        readonly=True,
        help='Technical name of the changed model.',
    )
    res_id = fields.Integer(
        string='Record ID',
        readonly=True,
        help='Database ID of the changed record.',
    )
    record_name = fields.Char(
        readonly=True,
        help='Display name of the changed record.',
    )
    field_id = fields.Many2one(
        comodel_name='ir.model.fields',
        readonly=True,
        help='Field that was changed.',
    )
    field_name = fields.Char(
        related='field_id.field_description',
        string='Field Name',
        readonly=True,
        help='Label of the changed field.',
    )
    old_value = fields.Char(
        readonly=True,
        help='Value before the change.',
    )
    new_value = fields.Char(
        readonly=True,
        help='Value after the change.',
    )
    changed_by = fields.Many2one(
        comodel_name='res.users',
        readonly=True,
        help='User who made the change.',
    )

    def init(self, _excluded_tables=None):
        """(Re)create the audit-trail SQL view over the regulated model tables."""
        excluded = set(_excluded_tables or ())
        # Every auditable model, whether it lives in pharmaceutical_base, in this
        # module or in an optional feature module. A table may legitimately be
        # missing: the feature module may not be installed, and on a fresh
        # install pharma_coa is only created later in this same registry pass
        # (the post_init_hook rebuilds the view once it exists).
        candidate_tables = {
            'pharma.bmr': 'pharma_bmr',
            'pharma.qc.test.order': 'pharma_qc_test_order',
            'pharma.coa': 'pharma_coa',
            'stock.lot': 'stock_lot',
            'pharma.sop': 'pharma_sop',
            'pharma.deviation': 'pharma_deviation',
            'pharma.capa': 'pharma_capa',
        }
        model_tables = {
            model: table
            for model, table in candidate_tables.items()
            if table not in excluded and table_exists(self.env.cr, table)
        }

        when_clauses = (
            SQL(' ').join(
                SQL(
                    "WHEN m.model = %s THEN (SELECT name FROM %s WHERE id = m.res_id)",
                    model,
                    SQL.identifier(table),
                )
                for model, table in model_tables.items()
            )
            if model_tables
            else SQL("WHEN FALSE THEN NULL")
        )
        model_in_list = (
            SQL(', ').join(SQL('%s', model) for model in model_tables) if model_tables else SQL('NULL')
        )

        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            SQL(
                """
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    v.id AS id,
                    m.date AS changed_on,
                    im.id AS model_id,
                    m.res_id AS res_id,
                    CASE
                    %s ELSE 'Unknown'
                    END AS record_name,
                    v.field_id AS field_id,
                    COALESCE(
                        v.old_value_char,
                        v.old_value_text,
                        CAST(v.old_value_integer AS VARCHAR),
                        CAST(v.old_value_float AS VARCHAR),
                        CAST(v.old_value_datetime AS VARCHAR)
                    ) AS old_value,
                    COALESCE(
                        v.new_value_char,
                        v.new_value_text,
                        CAST(v.new_value_integer AS VARCHAR),
                        CAST(v.new_value_float AS VARCHAR),
                        CAST(v.new_value_datetime AS VARCHAR)
                    ) AS new_value,
                    m.create_uid AS changed_by
                FROM mail_tracking_value v
                JOIN mail_message m ON v.mail_message_id = m.id
                LEFT JOIN ir_model im ON im.model = m.model
                WHERE m.model IN (%s)
            )
        """,
                SQL.identifier(self._table),
                when_clauses,
                model_in_list,
            )
        )
