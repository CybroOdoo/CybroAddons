# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Arjun S (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU AFFERO GENERAL PUBLIC LICENSE (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import models


def get_query(self, args, operation, field, start_date=None, end_date=None,
              group_by=False, apply_ir_rules=False):
    """Dashboard Block Query Builder"""
    query = self._search(args)
    if apply_ir_rules:
        self._apply_ir_rules(query, 'read')
    # from_clause/where_clause are odoo.tools.sql.SQL objects in Odoo 17+,
    # not strings — pull out .code (the actual SQL text) and .params.
    from_clause, from_params = query.from_clause.code, query.from_clause.params
    where_clause, where_params = query.where_clause.code, query.where_clause.params
    select_parts = []

    join_parts = []
    group_by_parts = []
    if operation and field:
        select_parts.append(f"COALESCE({operation.upper()}(\"{self._table}\".{field.name}), 0) AS value")
    else:
        select_parts.append(f"\"{self._table}\".id")
    if group_by:
        if group_by.name == 'product_id':
            join_parts += [
                f'INNER JOIN product_product ON product_product.id = "{self._table}".product_id',
                'INNER JOIN product_template ON product_template.id = product_product.product_tmpl_id'
            ]
            select_parts.append('product_template.name AS product_name')
            group_by_parts.append('product_template.name')
        elif group_by.name == 'categ_id':
            join_parts += [
                f'INNER JOIN product_product ON product_product.id = "{self._table}".product_id',
                'INNER JOIN product_template ON product_template.id = product_product.product_tmpl_id',
                'INNER JOIN product_category ON product_category.id = product_template.categ_id'
            ]
            select_parts.append('product_category.complete_name AS categ_name')
            group_by_parts.append('product_category.complete_name')
        elif group_by.ttype == 'many2one':
            rel_model = group_by.relation.replace('.', '_')
            rec_name = self.env[group_by.relation]._rec_name_fallback()
            join_parts.append(f'INNER JOIN {rel_model} ON "{rel_model}".id = "{self._table}".{group_by.name}')
            select_parts.append(f'"{rel_model}".{rec_name} AS {group_by.name}')
            group_by_parts.append(f'"{rel_model}".{rec_name}')
        else:
            select_parts.append(f'"{self._table}".{group_by.name}')
            group_by_parts.append(f'"{self._table}".{group_by.name}')
    where_clauses = []
    params = list(from_params)
    if where_clause:
        params += list(where_params)
        where_clauses.append(where_clause)
    if start_date and start_date != 'null':
        where_clauses.append(f'"{self._table}".create_date >= %s')
        params.append(start_date)
    if end_date and end_date != 'null':
        where_clauses.append(f'"{self._table}".create_date <= %s')
        params.append(end_date)
    where_str = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    group_by_str = f" GROUP BY {', '.join(group_by_parts)}" if group_by_parts else ""
    query_str = f"""
        SELECT {', '.join(select_parts)}
        FROM {from_clause}
        {' '.join(join_parts)}
        {where_str}
        {group_by_str}
    """
    return self._cr.mogrify(query_str, tuple(params)).decode()

models.BaseModel.get_query = get_query

