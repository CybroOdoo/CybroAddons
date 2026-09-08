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
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class WmWasteCategory(models.Model):
    """Master data model defining waste material categories, regulatory codes, and associated compliance rules."""
    _name = 'wm.waste.category'
    _description = 'Waste Category'
    _order = 'sequence, name'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'wm.audit.mixin']

    name = fields.Char(string='Name', help='Provides information about name', required=True)
    code = fields.Char(string='Code', help='Provides information about code')
    sequence = fields.Integer(string='Sequence', help='Provides information about sequence', default=10)
    active = fields.Boolean(string='Active', help='Provides information about active', default=True)
    company_id = fields.Many2one('res.company', string='Company', help='Provides information about company', default=lambda self: self.env.company)
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
        string='EPA WARM Factor (tCO2e/MT)',
        default=1.50,
        digits=(6, 3),
        help='EPA Waste Reduction Model (WARM) emission factor: Metric tons of CO2 equivalent (tCO2e) avoided per metric ton (1,000 kg) of waste recycled vs. landfilled.'
    )
    description = fields.Text(string='Description')

    def _auto_init(self):
        """
        Auto-clean existing duplicate categories in the database before
        applying constraints.
        """
        cr = self.env.cr
        from odoo.tools import sql
        if sql.table_exists(cr, self._table):
            try:
                with cr.savepoint():
                    cr.execute("""
                        SELECT LOWER(TRIM(name)) AS norm_name, array_agg(id ORDER BY id ASC) AS ids
                        FROM wm_waste_category
                        WHERE name IS NOT NULL AND name != ''
                        GROUP BY LOWER(TRIM(name))
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
                                for fk in fk_refs:
                                    tbl, col = fk['table_name'], fk['column_name']
                                    if sql.table_exists(cr, tbl) and sql.column_exists(cr, tbl, col):
                                        with cr.savepoint():
                                            # Clean duplicate entries in M2M junction tables if applicable
                                            cr.execute(f"DELETE FROM {tbl} WHERE {col} = %s AND EXISTS (SELECT 1 FROM {tbl} t2 WHERE t2.{col} = %s)", (r_id, keep_id))
                                            cr.execute(f"UPDATE {tbl} SET {col} = %s WHERE {col} = %s", (keep_id, r_id))

                                with cr.savepoint():
                                    cr.execute("DELETE FROM ir_model_data WHERE model = %s AND res_id = %s", ('wm.waste.category', r_id))
                                with cr.savepoint():
                                    cr.execute("DELETE FROM wm_waste_category WHERE id = %s", (r_id,))
            except Exception as e:
                _logger.warning("wm_waste_category: Error during deduplication in _auto_init: %s", e)
        return super()._auto_init()

    _name_uniq = models.Constraint('UNIQUE (name)', 'A waste category with the same name already exists!')
    _code_uniq = models.Constraint('UNIQUE (code)', 'A waste category with the same code already exists!')

    @api.constrains('name', 'code')
    def _check_unique_category(self):
        """ Ensure no duplicate category names or codes exist (case-insensitive check). """
        for cat in self:
            if cat.name:
                dup_name = self.search([
                    ('id', '!=', cat.id),
                    ('name', '=ilike', cat.name.strip())
                ], limit=1)
                if dup_name:
                    raise ValidationError(_("A waste category named '%s' already exists.") % cat.name)
            if cat.code:
                dup_code = self.search([
                    ('id', '!=', cat.id),
                    ('code', '=ilike', cat.code.strip())
                ], limit=1)
                if dup_code:
                    raise ValidationError(_("A waste category with code '%s' already exists.") % cat.code)
