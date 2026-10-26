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
import logging

import psycopg2

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import SQL, sql

_logger = logging.getLogger(__name__)


class WmWasteCategory(models.Model):
    """Master data for waste categories with code, pricing, default processing method and emission factor."""
    _name = 'wm.waste.category'
    _description = 'Waste Category'
    _order = 'sequence, name'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'wm.audit.mixin']

    name = fields.Char(help='Provides information about name', required=True)
    code = fields.Char(help='Provides information about code')
    sequence = fields.Integer(help='Provides information about sequence', default=10)
    active = fields.Boolean(help='Provides information about active', default=True)
    company_id = fields.Many2one('res.company', help='Provides information about company', default=lambda self: self.env.company)
    material_ids = fields.Many2many(
        'product.product',
        string='Available Materials'
    )
    product_ids = fields.One2many(
        'product.template',
        'wm_waste_category_id',
        string='Products',
        help='Products associated with this waste category'
    )
    price = fields.Float(string='Price per kg')
    service_product_id = fields.Many2one(
        'product.product',
        string='Quotation/Invoice Product',
        domain="[('type', '=', 'service')]",
        help='Service product used to represent this category on quotations '
             'and invoices when no specific material product is selected.',
    )
    default_processing = fields.Selection([
        ('sort', 'Sort'),
        ('recycle', 'Recycle'),
        ('dispose', 'Dispose'),
        ('compost', 'Compost'),
        ('hazardous_treatment', 'Hazardous Treatment'),
    ], string='Default Processing Method', default='sort')
    auto_create_batches_on_collection = fields.Boolean(string='Auto-Create Batches on Collection', default=True)

    warm_factor_co2 = fields.Float(
        string='CO2e Factor (tCO2e/t)',
        default=0.0,
        digits=(6, 3),
        help='Metric tons of CO2 equivalent (tCO2e) avoided per metric ton (1,000 kg) of this waste '
             'recycled instead of landfilled. Enter a factor from a recognised source, such as the '
             'EPA Waste Reduction Model (WARM); CO2 savings are reported as zero until it is set.'
    )
    description = fields.Text()

    def _auto_init(self):
        """
        Auto-clean existing duplicate categories in the database before
        applying constraints.
        """
        self._merge_duplicate_categories()
        return super()._auto_init()

    def _merge_duplicate_categories(self):
        """
        Merge categories of the same company whose names only differ by
        case/whitespace into the
        oldest (or XML-defined) one: references are repointed, and a duplicate
        is deleted only once nothing references it any more.
        """
        cr = self.env.cr
        if sql.table_exists(cr, self._table):
            try:
                with cr.savepoint():
                    cr.execute("""
                        SELECT LOWER(TRIM(name)) AS norm_name, array_agg(id ORDER BY id ASC) AS ids
                        FROM wm_waste_category
                        WHERE name IS NOT NULL AND name != ''
                        GROUP BY LOWER(TRIM(name)), company_id
                        HAVING COUNT(*) > 1
                    """)
                    duplicates = cr.dictfetchall()
                    if duplicates:
                        # Find all foreign keys pointing to wm_waste_category in the database
                        cr.execute("""
                            SELECT
                                c.conrelid::regclass::text AS table_name,
                                a.attname AS column_name
                            FROM pg_constraint c
                            JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey)
                            WHERE c.contype = 'f' AND c.confrelid = 'wm_waste_category'::regclass
                        """)
                        fk_refs = cr.dictfetchall()

                        for row in duplicates:
                            ids = row['ids']
                            # Prefer the ID recorded in ir_model_data (from base XML data)
                            cr.execute("""
                                SELECT res_id FROM ir_model_data
                                WHERE model = 'wm.waste.category' AND res_id = ANY(%s)
                                ORDER BY id ASC LIMIT 1
                            """, (ids,))
                            imd = cr.fetchone()
                            keep_id = imd[0] if imd else ids[0]
                            remove_ids = [i for i in ids if i != keep_id]

                            for r_id in remove_ids:
                                still_referenced = False
                                for fk in fk_refs:
                                    tbl, col = fk['table_name'], fk['column_name']
                                    if not (sql.table_exists(cr, tbl) and sql.column_exists(cr, tbl, col)):
                                        continue
                                    other_cols = [
                                        c for c in sql.table_columns(cr, tbl) if c != col
                                    ]
                                    # Many2many junction tables (no id, one other column): drop
                                    # the duplicate's row only when the same pair already
                                    # exists for the kept category. Rows of regular tables are
                                    # never deleted, only repointed.
                                    is_junction = 'id' not in other_cols and len(other_cols) == 1
                                    try:
                                        with cr.savepoint():
                                            if is_junction:
                                                other = other_cols[0]
                                                cr.execute(SQL(
                                                    'DELETE FROM %(tbl)s t WHERE t.%(col)s = %(r_id)s AND EXISTS '
                                                    '(SELECT 1 FROM %(tbl)s t2 WHERE t2.%(col)s = %(keep_id)s '
                                                    'AND t2.%(other)s = t.%(other)s)',
                                                    tbl=SQL.identifier(tbl), col=SQL.identifier(col),
                                                    other=SQL.identifier(other), r_id=r_id, keep_id=keep_id))
                                            cr.execute(SQL(
                                                'UPDATE %(tbl)s SET %(col)s = %(keep_id)s WHERE %(col)s = %(r_id)s',
                                                tbl=SQL.identifier(tbl), col=SQL.identifier(col),
                                                keep_id=keep_id, r_id=r_id))
                                    except psycopg2.Error as e:
                                        _logger.warning("wm_waste_category: could not repoint %s.%s from %s to %s: %s",
                                                        tbl, col, r_id, keep_id, e)
                                    cr.execute(SQL(
                                        'SELECT 1 FROM %s WHERE %s = %s LIMIT 1',
                                        SQL.identifier(tbl), SQL.identifier(col), r_id))
                                    if cr.fetchone():
                                        still_referenced = True

                                if still_referenced:
                                    # Deleting it would cascade-delete (or block on) the rows
                                    # that could not be moved: keep it and let an admin merge.
                                    _logger.warning("wm_waste_category: duplicate category %s kept, it is still referenced", r_id)
                                    continue
                                with cr.savepoint():
                                    cr.execute("DELETE FROM ir_model_data WHERE model = %s AND res_id = %s", ('wm.waste.category', r_id))
                                with cr.savepoint():
                                    cr.execute("DELETE FROM wm_waste_category WHERE id = %s", (r_id,))
            except psycopg2.Error as e:
                _logger.warning("wm_waste_category: Error during deduplication in _auto_init: %s", e)

    # Categories are company-scoped: names/codes are unique per company
    _name_uniq = models.Constraint('UNIQUE (name, company_id)', 'A waste category with the same name already exists!')
    _code_uniq = models.Constraint('UNIQUE (code, company_id)', 'A waste category with the same code already exists!')

    @api.constrains('name', 'code', 'company_id')
    def _check_unique_category(self):
        """
        Ensure no duplicate category names or codes exist (case-insensitive
        check) among the categories visible to the same company: those of
        that company and the shared ones (a shared category clashes with
        every company). Searched as superuser so other users' record rules
        cannot hide a duplicate.
        """
        Category = self.sudo()
        for cat in self:
            company_domain = [('company_id', 'in', [cat.company_id.id, False])] if cat.company_id else []
            if cat.name:
                dup_name = Category.search([
                    ('id', '!=', cat.id),
                    ('name', '=ilike', cat.name.strip())
                ] + company_domain, limit=1)
                if dup_name:
                    raise ValidationError(self.env._("A waste category named '%s' already exists.", cat.name))
            if cat.code:
                dup_code = Category.search([
                    ('id', '!=', cat.id),
                    ('code', '=ilike', cat.code.strip())
                ] + company_domain, limit=1)
                if dup_code:
                    raise ValidationError(self.env._("A waste category with code '%s' already exists.", cat.code))
