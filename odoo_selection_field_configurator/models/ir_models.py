# -*- coding: utf-8 -*-
###############################################################################
#
#   Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#   Author: Ammu Raj( odoo@cybrosys.com )
#
#   You can modify it under the terms of the GNU AFFERO
#   GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#   You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#   (AGPL v3) along with this program.
#   If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from psycopg2 import sql
from odoo import api
from odoo.exceptions import UserError
from odoo.fields import Selection
from odoo.tools.translate import _
from odoo.addons.base.models.ir_model import IrModelFields
from odoo.addons.base.models.ir_model import IrModelSelection


def convert_to_cache(self, value, record, validate=True):
    """
    Monkey patched the function convert_to_cache and added condition to check
    value in by search get all selections of that field
    """
    if not validate:
        return value or None
    if value and self.column_type[0] == 'int4':
        value = int(value)
    if value in self.get_values(record.env):
        return value
    elif not value:
        return None
    if self.type == 'selection':
        field_id = record.env['ir.model.fields'].search(
            [('model', '=', str(self).rsplit(".", 1)[0]),
             ('name', '=', str(self).rsplit(".", 1)[1])]).id
        value_list = [i.value for i in
                      record.env['ir.model.fields.selection'].search(
                          [('field_id', '=', field_id)])]
        if value in value_list:
            return value
    raise UserError(
        _("User Error: Custom selection requires Python code implementation, "
          "preferably through a custom addon to provide the desired "
          "functionalities.."))


Selection.convert_to_cache = convert_to_cache


def write(self, vals):
    """
    Monkey Patching the write function to remove raise error for editing in
    base fields
    """
    # If set, *one* column can be renamed here
    column_rename = None
    patched_models = set()
    if vals and self:
        for item in self:
            if vals.get('model_id', item.model_id.id) != item.model_id.id:
                raise UserError(
                    _("Changing the model of a field is forbidden!"))
            if vals.get('ttype', item.ttype) != item.ttype:
                raise UserError(
                    _("Changing the type of a field is not yet supported. "
                      "Please drop it and create it again!"))
            obj = self.pool.get(item.model)
            field = getattr(obj, '_fields', {}).get(item.name)
            if vals.get('name', item.name) != item.name:
                # We need to rename the field
                item._prepare_update()
                if item.ttype in ('one2many', 'many2many', 'binary'):
                    # Those field names are not explicit in the database!
                    pass
                else:
                    if column_rename:
                        raise UserError(
                            _('Can only rename one field at a time!'))
                    column_rename = (
                        obj._table, item.name, vals['name'], item.index,
                        item.store)
            # We don't check the 'state', because it might come from the context
            # (thus be set for multiple fields) and will be ignored anyway.
            if obj is not None and field is not None:
                patched_models.add(obj._name)
    # These shall never be written (modified)
    for column_name in ('model_id', 'model', 'state'):
        if column_name in vals:
            del vals[column_name]
    res = super(IrModelFields, self).write(vals)
    self.flush()
    if column_rename:
        # Rename column in database, and its corresponding index if present
        table, oldname, newname, index, stored = column_rename
        if stored:
            self._cr.execute(
                sql.SQL('ALTER TABLE {} RENAME COLUMN {} TO {}').format(
                    sql.Identifier(table),
                    sql.Identifier(oldname),
                    sql.Identifier(newname)))
            if index:
                self._cr.execute(
                    sql.SQL('ALTER INDEX {} RENAME TO {}').format(
                        sql.Identifier(f'{table}_{oldname}_index'),
                        sql.Identifier(f'{table}_{newname}_index'), ))
    if column_rename or patched_models:
        # Setup models, this will reload all manual fields in registry
        self.flush()
        self.pool.setup_models(self._cr)
    if patched_models:
        # Update the database schema of the models to patch
        models = self.pool.descendants(patched_models, '_inherits')
        self.pool.init_models(self._cr, models, dict(self._context,
                                                     update_custom_fields=True))
    return res


IrModelFields.write = write


@api.model_create_multi
def create(self, vals_list):
    """
    Monkey Patching the create function to remove raise error for editing in
    base fields
    """
    field_ids = {vals['field_id'] for vals in vals_list}
    field_names = set()
    for field in self.env['ir.model.fields'].browse(field_ids):
        field_names.add((field.model, field.name))
    recs = super(IrModelSelection, self).create(vals_list)
    if any(model in self.pool and name in self.pool[model]._fields
           for model, name in field_names):
        # Setup models; this re-initializes model in registry
        self.flush()
        self.pool.setup_models(self._cr)
    return recs


IrModelSelection.create = create


@api.ondelete(at_uninstall=False)
def _unlink_if_manual(self):
    """
    Monkey Patching the _unlink_if_manual function to remove raise error for
    editing in base fields
    """
    pass


IrModelSelection._unlink_if_manual = _unlink_if_manual
