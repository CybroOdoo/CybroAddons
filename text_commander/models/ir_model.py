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
from odoo import api, models
from odoo.exceptions import AccessError, UserError


class IrModel(models.Model):
    """ Class to check the model and get the record values as specified by
    the user """
    _inherit = 'ir.model'

    @api.model
    def check_model(self, data):
        """ Check model from frontend """
        if not data:
            return []
        data_str = str(data).strip()
        # 1. Search by model description using ORM
        model_rec = self.env['ir.model'].search(
            [('name', '=ilike', data_str)], limit=1,
        )
        if not model_rec:
            # 2. Search by technical model name (e.g. sale.order)
            model_rec = self.env['ir.model'].search(
                [('model', '=ilike', data_str)], limit=1,
            )
        if not model_rec:
            # 3. Parameterized SQL fallback for JSONB translated name
            user_lang = self.env.lang or 'en_US'
            self.env.cr.execute(
                """SELECT model, name FROM ir_model
                   WHERE lower(name->>'en_US') = lower(%s)
                      OR lower(name->>%s) = lower(%s)
                      OR lower(model) = lower(%s) LIMIT 1""",
                (data_str, user_lang, data_str, data_str),
            )
            res = self.env.cr.dictfetchall()
            if res:
                return res
            return []
        return [{'model': model_rec.model, 'name': model_rec.name}]

    @api.model
    def get_records(self, data):
        """ Function for fetching record from database using ORM """
        model_name = data.get('model')
        if not model_name or model_name not in self.env:
            return []

        model_pool = self.env[model_name]

        # Validate caller read access
        try:
            model_pool.check_access('read')
        except (AccessError, UserError):
            return []

        if data.get('regex') == 1:
            search_val = (data.get('record') or '').strip()
            if not search_val:
                return []
            rec_name = model_pool._rec_name or 'name'

            # 1. ORM search by rec_name
            if rec_name in model_pool._fields:
                try:
                    res_ids = model_pool.search(
                        [(rec_name, 'ilike', search_val)],
                    ).ids
                    if res_ids:
                        return res_ids
                except (AccessError, UserError):
                    pass

            # 2. ORM search by display_name
            if 'display_name' in model_pool._fields and rec_name != 'display_name':
                try:
                    res_ids = model_pool.search(
                        [('display_name', 'ilike', search_val)],
                    ).ids
                    if res_ids:
                        return res_ids
                except (AccessError, UserError):
                    pass

            return []

        if data.get('regex') == 2:
            field_name = data.get('field')
            field_type = data.get('field_type')
            field_string = (data.get('field_string') or '').strip()

            # Strict validation: field must exist on target model
            if not field_name or field_name not in model_pool._fields:
                return []

            fld = model_pool._fields[field_name]

            if field_type == 'many2one' or fld.type == 'many2one':
                rel_model_name = (
                    getattr(fld, 'comodel_name', None)
                    or data.get('field_relation')
                    or ''
                )

                if not rel_model_name:
                    field_rec = self.env['ir.model.fields'].search([
                        ('model', '=', model_name),
                        ('name', '=', field_name),
                    ], limit=1)
                    if field_rec and field_rec.relation:
                        rel_model_name = field_rec.relation

                rel_ids = set()
                if rel_model_name and rel_model_name in self.env:
                    rel_pool = self.env[rel_model_name]

                    # ORM search on related model
                    for col in ('name', 'display_name', 'complete_name'):
                        if col in rel_pool._fields:
                            try:
                                rel_ids.update(
                                    rel_pool.search(
                                        [(col, 'ilike', field_string)],
                                    ).ids,
                                )
                            except (AccessError, UserError):
                                pass

                    # For res.partner include child/commercial contacts
                    if rel_model_name == 'res.partner' and rel_ids:
                        try:
                            contacts = rel_pool.search([
                                '|',
                                ('parent_id', 'in', list(rel_ids)),
                                ('commercial_partner_id', 'in',
                                 list(rel_ids)),
                            ]).ids
                            rel_ids.update(contacts)
                        except (AccessError, UserError):
                            pass

                # Search target model by related record IDs using ORM
                if rel_ids:
                    try:
                        res_ids = model_pool.search(
                            [(field_name, 'in', list(rel_ids))],
                        ).ids
                        if res_ids:
                            return res_ids
                    except (AccessError, UserError):
                        pass

                # Direct relational searches on target model via ORM dotted paths
                search_domains = [
                    [(f"{field_name}.name", 'ilike', field_string)],
                    [(f"{field_name}.display_name", 'ilike', field_string)],
                    [(field_name, 'ilike', field_string)],
                ]
                if rel_model_name == 'res.partner':
                    search_domains.extend([
                        [(f"{field_name}.parent_id.name",
                          'ilike', field_string)],
                        [(f"{field_name}.commercial_partner_id.name",
                          'ilike', field_string)],
                    ])
                for domain in search_domains:
                    try:
                        res_ids = model_pool.search(domain).ids
                        if res_ids:
                            return res_ids
                    except (AccessError, UserError):
                        continue

                return []

            if field_type == 'selection' or fld.type == 'selection':
                target_val = field_string
                for state, label in self._get_selection_values(data):
                    if (target_val.lower() == str(label).lower()
                            or target_val.lower() == str(state).lower()):
                        target_val = state
                        break
                try:
                    return model_pool.search(
                        [(field_name, '=', target_val)],
                    ).ids
                except (AccessError, UserError):
                    return []

            # Standard ORM search for other field types
            try:
                return model_pool.search(
                    [(field_name, 'ilike', field_string)],
                ).ids
            except (AccessError, UserError):
                return []

        return []

    def _get_selection_values(self, data):
        """ Function for getting selection values"""
        model_name = data.get('model')
        field_name = data.get('field')
        if model_name and model_name in self.env:
            model_pool = self.env[model_name]
            if field_name in model_pool._fields:
                field_info = model_pool.fields_get([field_name])
                return (
                    field_info.get(field_name, {}).get('selection', [])
                    or []
                )
        return []

    @api.model
    def check_fields_model(self, data):
        """Function for checking field of a model"""
        model_name = data.get('model')
        field_tokens = data.get('field_string', [])
        if not model_name or not field_tokens:
            return []

        has_model = model_name in self.env
        model_pool = self.env[model_name] if has_model else None
        user_lang = self.env.lang or 'en_US'
        string = ""
        for rec in range(len(field_tokens)):
            if rec != 0:
                string += " " + field_tokens[rec]
            else:
                string += field_tokens[rec]

            # 1. Check ir.model.fields via ORM
            field_rec = self.env['ir.model.fields'].search([
                ('model', '=', model_name),
                '|',
                ('field_description', '=ilike', string),
                ('name', '=ilike', string),
            ], limit=1)
            if field_rec:
                return [{
                    'name': field_rec.name,
                    'ttype': field_rec.ttype,
                    'relation': field_rec.relation or '',
                    'del': string,
                }]

            # 2. Check model's in-memory fields dictionary
            if model_pool is not None:
                for fname, fld in model_pool._fields.items():
                    if (fld.string
                            and fld.string.strip().lower() == string.lower()):
                        rel = self._resolve_comodel(
                            model_name, fname, fld,
                        )
                        return [{
                            'name': fname,
                            'ttype': fld.type,
                            'relation': rel,
                            'del': string,
                        }]
                if string.lower() in model_pool._fields:
                    fld = model_pool._fields[string.lower()]
                    rel = self._resolve_comodel(
                        model_name, string.lower(), fld,
                    )
                    return [{
                        'name': string.lower(),
                        'ttype': fld.type,
                        'relation': rel,
                        'del': string,
                    }]

            # 3. Fallback parameterized SQL for translated field description
            self.env.cr.execute(
                """SELECT name, ttype, relation FROM ir_model_fields
                   WHERE model = %s
                   AND (lower(field_description->>'en_US') = lower(%s)
                        OR lower(field_description->>%s) = lower(%s)
                        OR lower(name) = lower(%s)) LIMIT 1""",
                (model_name, string, user_lang, string, string),
            )
            res = self.env.cr.dictfetchall()
            if res:
                res[0]['del'] = string
                return res

        return []

    def _resolve_comodel(self, model_name, field_name, fld):
        """Resolve comodel name for a relational field."""
        rel = (
            getattr(fld, 'comodel_name', None)
            or getattr(fld, 'relation', None)
            or getattr(fld, '_description_relation', None)
            or ''
        )
        if rel:
            return rel
        # Fallback: check ir.model.fields
        field_rec = self.env['ir.model.fields'].search([
            ('model', '=', model_name),
            ('name', '=', field_name),
        ], limit=1)
        return field_rec.relation or ''
