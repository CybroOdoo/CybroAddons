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


class PharmaAuditTrail(models.Model):
    """Read-only audit trail of changes across the regulated pharma models."""
    _name = 'pharma.audit.trail'
    _description = 'Audit Trail'
    _auto = False
    _order = 'changed_on desc'

    changed_on = fields.Datetime(
        string='Changed On',
        readonly=True,
        help='Specifies the Changed On for this record.',
    )
    model_id = fields.Many2one(
        comodel_name='ir.model',
        string='Model Name',
        readonly=True,
        help='Specifies the Model Name for this record.',
    )
    model = fields.Char(
        related='model_id.model',
        string='Model Technical Name',
        readonly=True,
        help='Specifies the Model Technical Name for this record.',
    )
    res_id = fields.Integer(
        string='Record ID',
        readonly=True,
        help='Specifies the Record ID for this record.',
    )
    record_name = fields.Char(
        string='Record Name',
        readonly=True,
        help='Specifies the Record Name for this record.',
    )
    field_id = fields.Many2one(
        comodel_name='ir.model.fields',
        string='Field',
        readonly=True,
        help='Specifies the Field for this record.',
    )
    field_name = fields.Char(
        related='field_id.field_description',
        string='Field Name',
        readonly=True,
        help='Specifies the Field Name for this record.',
    )
    old_value = fields.Char(
        string='Old Value',
        readonly=True,
        help='Specifies the Old Value for this record.',
    )
    new_value = fields.Char(
        string='New Value',
        readonly=True,
        help='Specifies the New Value for this record.',
    )
    changed_by = fields.Many2one(
        comodel_name='res.users',
        string='Changed By',
        readonly=True,
        help='Specifies the Changed By for this record.',
    )

    def init(self, _excluded_tables=None):
        """(Re)create the audit-trail SQL view over the regulated model tables."""
        excluded = set(_excluded_tables or ())
        # Models that are always present (core pharmaceutical_base + this module).
        model_tables = {
            'pharma.bmr': 'pharma_bmr',
            'pharma.qc.test.order': 'pharma_qc_test_order',
            'pharma.coa': 'pharma_coa',
            'stock.lot': 'stock_lot',
        }
        # Optional models: only audited when their feature module (and hence its
        # table) is installed.
        optional_model_tables = {
            'pharma.sop': 'pharma_sop',
            'pharma.deviation': 'pharma_deviation',
            'pharma.capa': 'pharma_capa',
        }
        for model, table in optional_model_tables.items():
            if table in excluded:
                continue
            self.env.cr.execute(
                "SELECT 1 FROM information_schema.tables WHERE table_name = %s",
                (table,),
            )
            if self.env.cr.fetchone():
                model_tables[model] = table

        when_clauses = "\n".join(
            "                        WHEN m.model = '%s' THEN "
            "(SELECT name FROM %s WHERE id = m.res_id)" % (model, table)
            for model, table in model_tables.items()
        )
        model_in_list = ", ".join("'%s'" % model for model in model_tables)

        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
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
        """ % (self._table, when_clauses, model_in_list))
