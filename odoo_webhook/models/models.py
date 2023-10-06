# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Unnimaya C O (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
import json
import requests
from collections import defaultdict
from operator import attrgetter
from requests.exceptions import MissingSchema
from odoo import api, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError, AccessError
from odoo.models import BaseModel, _unlink, LOG_ACCESS_COLUMNS, \
    INSERT_BATCH_SIZE, SQL_DEFAULT
from odoo.tools import OrderedSet, split_every, attrgetter, clean_context


@api.model
def _create(self, data_list):
    """ Override _create method for sending the payload to the registered
    webhook url. When a new record is added to the model, it will check
    whether the model is added to webhook_webhook model. If it is added,
    the payload will be posted to the create_url."""
    assert data_list
    cr = self.env.cr
    # insert rows in batches of maximum INSERT_BATCH_SIZE
    ids = []  # ids of created records
    other_fields = OrderedSet()  # non-column fields
    for data_sublist in split_every(INSERT_BATCH_SIZE, data_list):
        stored_list = [data['stored'] for data in data_sublist]
        fnames = sorted({name for stored in stored_list for name in stored})
        columns = []
        rows = [[] for _ in stored_list]
        for fname in fnames:
            field = self._fields[fname]
            if field.column_type:
                columns.append(fname)
                for stored, row in zip(stored_list, rows):
                    if fname in stored:
                        colval = field.convert_to_column(stored[fname], self,
                                                         stored)
                        if field.translate is True and colval:
                            if 'en_US' not in colval.adapted:
                                colval.adapted['en_US'] = next(
                                    iter(colval.adapted.values()))
                        row.append(colval)
                    else:
                        row.append(SQL_DEFAULT)
            else:
                other_fields.add(field)
            if field.type == 'properties':
                # force calling fields.create for properties field because
                # we might want to update the parent definition
                other_fields.add(field)
        if not columns:
            # manage the case where we create empty records
            columns = ['id']
            for row in rows:
                row.append(SQL_DEFAULT)
        header = ", ".join(f'"{column}"' for column in columns)
        template = ", ".join("%s" for _ in rows)
        cr.execute(
            f'INSERT INTO "{self._table}" ({header}) VALUES {template} '
            f'RETURNING "id"',
            [tuple(row) for row in rows],
        )
        ids.extend(id_ for id_, in cr.fetchall())

    # put the new records in cache, and update inverse fields, for many2one
    #
    # cachetoclear is an optimization to avoid modified()'s cost until
    # other_fields are processed
    cachetoclear = []
    records = self.browse(ids)
    inverses_update = defaultdict(list)  # {(field, value): ids}
    common_set_vals = set(
        LOG_ACCESS_COLUMNS + [self.CONCURRENCY_CHECK_FIELD, 'id',
                              'parent_path'])
    for data, record in zip(data_list, records):
        data['record'] = record
        # DLE P104: test_inherit.py, test_50_search_one2many
        vals = dict(
            {k: v for d in data['inherited'].values() for k, v in d.items()},
            **data['stored'])
        set_vals = common_set_vals.union(vals)
        for field in self._fields.values():
            if field.type in ('one2many', 'many2many'):
                self.env.cache.set(record, field, ())
            elif field.related and not field.column_type:
                self.env.cache.set(record, field,
                                   field.convert_to_cache(None, record))
            # DLE P123: `test_adv_activity`, `test_message_assignation_inbox`,
            # `test_message_log`, `test_create_mail_simple`, ...
            # Set `mail.message.parent_id` to False in cache, so it doesn't do
            # the useless SELECT when computing the modified of `child_ids`
            # in other words, if `parent_id` is not set, no other message
            # `child_ids` are impacted.
            # + avoid the fetch of fields which are False. e.g. if a boolean
            # field is not passed in vals and as no default set in the field
            # attributes, then we know it can be set to False in the cache in
            # the case of create.
            elif field.name not in set_vals and not field.compute:
                self.env.cache.set(record, field,
                                   field.convert_to_cache(None, record))
        for fname, value in vals.items():
            field = self._fields[fname]
            if field.type in ('one2many', 'many2many'):
                cachetoclear.append((record, field))
            else:
                cache_value = field.convert_to_cache(value, record)
                self.env.cache.set(record, field, cache_value)
                if field.type in ('many2one', 'many2one_reference') and \
                        self.pool.field_inverses[field]:
                    inverses_update[(field, cache_value)].append(record.id)
    for (field, value), record_ids in inverses_update.items():
        field._update_inverses(self.browse(record_ids), value)
    # update parent_path
    records._parent_store_create()
    # protect fields being written against recomputation
    protected = [(data['protected'], data['record']) for data in data_list]
    with self.env.protecting(protected):
        # mark computed fields as todo
        records.modified(self._fields, create=True)
        if other_fields:
            # discard default values from context for other fields
            others = records.with_context(clean_context(self._context))
            for field in sorted(other_fields, key=attrgetter('_sequence')):
                field.create([
                    (other, data['stored'][field.name])
                    for other, data in zip(others, data_list)
                    if field.name in data['stored']
                ])
            # mark fields to recompute
            records.modified([field.name for field in other_fields],
                             create=True)
        # if value in cache has not been updated by other_fields, remove it
        for record, field in cachetoclear:
            if self.env.cache.contains(record,
                                       field) and not self.env.cache.get(record,
                                                                         field):
                self.env.cache.remove(record, field)
    # check Python constraints for stored fields
    records._validate_fields(
        name for data in data_list for name in data['stored'])
    records.check_access_rule('create')
    webhook = self.env['webhook.webhook'].search(
        [('model_id', '=', self.env['ir.model'].sudo().search(
            [('model', '=', records._name)]).id)]).filtered(
        lambda r: r.create_url).mapped(
        'create_url')
    if webhook:
        # Create payload if the model is added to webhook
        for rec in records:
            val_list = rec.search_read([('id', '=', rec.id)])
            for item in val_list[0].keys():
                field = (self.env['ir.model.fields'].sudo().search(
                    [('model', '=', rec._name), ('name', '=', item)]))
                if field.ttype == 'binary':
                    if val_list[0][field.name]:
                        base_url = self.env[
                            'ir.config_parameter'].sudo().get_param(
                            'web.base.url')
                        val_list[0][field.name] = (
                            f'{base_url}/web/image/{self._name}/'
                            f'{val_list[0]["id"]}'
                            f'/{field.name}')
            for item in webhook:
                # Post payload to the registered url
                requests.post(item, data=json.dumps(val_list[0],
                                                    default=str),
                              headers={
                                  'Content-Type': 'application/json'})
                try:
                    requests.post(item,
                                  data=json.dumps(val_list[0], default=str),
                                  headers={'Content-Type': 'application/json'})
                except MissingSchema:
                    raise ValidationError("Please check the Webhook Url for "
                                          "Create Event")
    return records


def unlink(self):
    """Override unlink method for sending the payload to the registered
    webhook url. When a record is deleted from a model, it will check
    whether the model is added to the webhook_webhook model. If it is added,
    the payload will be posted to the delete_url."""
    if not self:
        return True
    self.check_access_rights('unlink')
    self.check_access_rule('unlink')
    from odoo.addons.base.models.ir_model import MODULE_UNINSTALL_FLAG
    for func in self._ondelete_methods:
        # func._ondelete is True if it should be called during uninstallation
        if func._ondelete or not self._context.get(MODULE_UNINSTALL_FLAG):
            func(self)
    # TO FIX: this avoids an infinite loop when trying to recompute a
    # field, which triggers the recomputation of another field using the
    # same compute function, which then triggers again the computation
    # of those two fields
    for field in self._fields.values():
        self.env.remove_to_compute(field, self)
    self.env.flush_all()
    cr = self._cr
    Data = self.env['ir.model.data'].sudo().with_context({})
    Defaults = self.env['ir.default'].sudo()
    Property = self.env['ir.property'].sudo()
    Attachment = self.env['ir.attachment'].sudo()
    ir_property_unlink = Property
    ir_model_data_unlink = Data
    ir_attachment_unlink = Attachment
    # mark fields that depend on 'self' to recompute them after 'self' has
    # been deleted (like updating a sum of lines after deleting one line)
    with self.env.protecting(self._fields.values(), self):
        self.modified(self._fields, before=True)
    webhook = self.env['webhook.webhook'].search(
        [('model_id', '=', self.env['ir.model'].sudo().search(
            [('model', '=', self._name)]).id)]).filtered(
        lambda r: r.delete_url).mapped('delete_url')
    # Create payload of the model is added to webhook
    if webhook.delete_url:
        val_list = []
        for rec in self:
            val_list = rec.search_read([('id', '=', rec.id)])
            for item in val_list[0].keys():
                field = (self.env['ir.model.fields'].sudo().search(
                    [('model', '=', rec._name), ('name', '=', item)]))
                if field.ttype == 'binary':
                    if val_list[0][field.name]:
                        base_url = self.env[
                            'ir.config_parameter'].sudo().get_param(
                            'web.base.url')
                        val_list[0][field.name] = (f'{base_url}/web/image/'
                                                   f'{self._name}/{rec.id}'
                                                   f'/{field.name}')
        for rec in webhook:
            # Post payload to the registered url
            try:
                requests.post(rec, data=json.dumps(val_list[0], default=str),
                              headers={'Content-Type': 'application/json'})
            except MissingSchema:
                raise ValidationError(_("Please check the Webhook Url for "
                                        "Delete "
                                        "Event"))
    for sub_ids in cr.split_for_in_conditions(self.ids):
        records = self.browse(sub_ids)
        # Check if the records are used as default properties.
        refs = [f'{self._name},{id_}' for id_ in sub_ids]
        if Property.search(
                [('res_id', '=', False), ('value_reference', 'in', refs)],
                limit=1):
            raise UserError(
                _('Unable to delete this document because it is used as a '
                  'default property'))
        # Delete the records' properties.
        ir_property_unlink |= Property.search([('res_id', 'in', refs)])
        query = f'DELETE FROM "{self._table}" WHERE id IN %s'
        cr.execute(query, (sub_ids,))
        # Removing the ir_model_data reference if the record being deleted
        # is a record created by xml/csv file, as these are not connected
        # with real database foreign keys, and would be dangling references.
        #
        # Note: the following steps are performed as superuser to avoid
        # access rights restrictions, and with no context to avoid possible
        # side effects during admin calls.
        data = Data.search(
            [('model', '=', self._name), ('res_id', 'in', sub_ids)])
        ir_model_data_unlink |= data
        # For the same reason, remove the defaults having some of the
        # records as value
        Defaults.discard_records(records)
        # For the same reason, remove the relevant records in ir_attachment
        # (the search is performed with sql as the search method of
        # ir_attachment is overridden to hide attachments of deleted
        # records)
        query = ('SELECT id FROM ir_attachment WHERE res_model=%s AND'
                 ' res_id IN %s')
        cr.execute(query, (self._name, sub_ids))
        ir_attachment_unlink |= Attachment.browse(
            row[0] for row in cr.fetchall())
    # invalidate the *whole* cache, since the orm does not handle all
    # changes made in the database, like cascading delete!
    self.env.invalidate_all(flush=False)
    if ir_property_unlink:
        ir_property_unlink.unlink()
    if ir_model_data_unlink:
        ir_model_data_unlink.unlink()
    if ir_attachment_unlink:
        ir_attachment_unlink.unlink()
    # DLE P93: flush after unlink, for recompute fields depending on
    # the modified of unlink
    self.env.flush_all()
    # auditing: deletions are infrequent and leave no trace in the database
    _unlink.info('User #%s deleted %s records with IDs: %r', self._uid,
                 self._name, self.ids)
    return True


def write(self, vals):
    """ write(vals)

    Updates all records in ``self`` with the provided values.

    :param dict vals: fields to update and the value to set on them
    :raise AccessError: if user is not allowed to modify the specified
     records/fields
    :raise ValidationError: if invalid values are specified for selection fields
    :raise UserError: if a loop would be created in a hierarchy of objects a
    result of the operation (such as setting an object as its own parent)

    * For numeric fields (:class:`~odoo.fields.Integer`,
      :class:`~odoo.fields.Float`) the value should be of the
      corresponding type
    * For :class:`~odoo.fields.Boolean`, the value should be a
      :class:`python:bool`
    * For :class:`~odoo.fields.Selection`, the value should match the
      selection values (generally :class:`python:str`, sometimes
      :class:`python:int`)
    * For :class:`~odoo.fields.Many2one`, the value should be the
      database identifier of the record to set
    * The expected value of a :class:`~odoo.fields.One2many` or
      :class:`~odoo.fields.Many2many` relational field is a list of
      :class:`~odoo.fields.Command` that manipulate the relation the
      implement. There are a total of 7 commands:
      :meth:`~odoo.fields.Command.create`,
      :meth:`~odoo.fields.Command.update`,
      :meth:`~odoo.fields.Command.delete`,
      :meth:`~odoo.fields.Command.unlink`,
      :meth:`~odoo.fields.Command.link`,
      :meth:`~odoo.fields.Command.clear`, and
      :meth:`~odoo.fields.Command.set`.
    * For :class:`~odoo.fields.Date` and `~odoo.fields.Datetime`,
      the value should be either a date(time), or a string.

      .. warning::

        If a string is provided for Date(time) fields,
        it must be UTC-only and formatted according to
        :const:`odoo.tools.misc.DEFAULT_SERVER_DATE_FORMAT` and
        :const:`odoo.tools.misc.DEFAULT_SERVER_DATETIME_FORMAT`

    * Other non-relational fields use a string for value
    """
    if not self:
        return True

    self.check_access_rights('write')
    self.check_field_access_rights('write', vals.keys())
    self.check_access_rule('write')
    env = self.env

    bad_names = {'id', 'parent_path'}
    if self._log_access:
        # the superuser can set log_access fields while loading registry
        if not (self.env.uid == SUPERUSER_ID and not self.pool.ready):
            bad_names.update(LOG_ACCESS_COLUMNS)

    # set magic fields
    vals = {key: val for key, val in vals.items() if key not in bad_names}
    if self._log_access:
        vals.setdefault('write_uid', self.env.uid)
        vals.setdefault('write_date', self.env.cr.now())

    field_values = []  # [(field, value)]
    determine_inverses = defaultdict(list)  # {inverse: fields}
    fnames_modifying_relations = []
    protected = set()
    check_company = False
    for fname, value in vals.items():
        field = self._fields.get(fname)
        if not field:
            raise ValueError(
                "Invalid field %r on model %r" % (fname, self._name))
        field_values.append((field, value))
        if field.inverse:
            if field.type in ('one2many', 'many2many'):
                # The written value is a list of commands that must applied
                # on the field's current value. Because the field is
                # protected while being written, the field's current value
                # will not be computed and default to an empty recordset. So
                # make sure the field's value is in cache before writing, in
                # order to avoid an inconsistent update.
                self[fname]
            determine_inverses[field.inverse].append(field)
        if self.pool.is_modifying_relations(field):
            fnames_modifying_relations.append(fname)
        if field.inverse or (field.compute and not field.readonly):
            if field.store or field.type not in ('one2many', 'many2many'):
                # Protect the field from being recomputed while being
                # inversed. In the case of non-stored x2many fields, the
                # field's value may contain unexpeced new records (created
                # by command 0). Those new records are necessary for
                # inversing the field, but should no longer appear if the
                # field is recomputed afterwards. Not protecting the field
                # will automatically invalidate the field from the cache,
                # forcing its value to be recomputed once dependencies are
                # up-to-date.
                protected.update(self.pool.field_computed.get(field, [field]))
        if fname == 'company_id' or (field.relational and field.check_company):
            check_company = True

    # force the computation of fields that are computed with some assigned
    # fields, but are not assigned themselves
    to_compute = [field.name
                  for field in protected
                  if field.compute and field.name not in vals]
    if to_compute:
        self._recompute_recordset(to_compute)

    # protect fields being written against recomputation
    with env.protecting(protected, self):
        # Determine records depending on values. When modifying a relational
        # field, you have to recompute what depends on the field's values
        # before and after modification.  This is because the modification
        # has an impact on the "data path" between a computed field and its
        # dependency.  Note that this double call to modified() is only
        # necessary for relational fields.
        #
        # It is best explained with a simple example: consider two sales
        # orders SO1 and SO2.  The computed total amount on sales orders
        # indirectly depends on the many2one field 'order_id' linking lines
        # to their sales order.  Now consider the following code:
        #
        #   line = so1.line_ids[0]      # pick a line from SO1
        #   line.order_id = so2         # move the line to SO2
        #
        # In this situation, the total amount must be recomputed on *both*
        # sales order: the line's order before the modification, and the
        # line's order after the modification.
        self.modified(fnames_modifying_relations, before=True)

        real_recs = self.filtered('id')

        # field.write_sequence determines a priority for writing on fields.
        # Monetary fields need their corresponding currency field in cache
        # for rounding values. X2many fields must be written last, because
        # they flush other fields when deleting lines.
        for field, value in sorted(field_values,
                                   key=lambda item: item[0].write_sequence):
            field.write(self, value)

        # determine records depending on new values
        #
        # Call modified after write, because the modified can trigger a
        # search which can trigger a flush which can trigger a recompute
        # which remove the field from the recompute list while all the
        # values required for the computation could not be yet in cache.
        # e.g. Write on `name` of `res.partner` trigger the recompute of
        # `display_name`, which triggers a search on child_ids to find the
        # childs to which the display_name must be recomputed, which
        # triggers the flush of `display_name` because the _order of
        # res.partner includes display_name. The computation of display_name
        # is then done too soon because the parent_id was not yet written.
        # (`test_01_website_reset_password_tour`)
        self.modified(vals)

        if self._parent_store and self._parent_name in vals:
            self.flush_model([self._parent_name])

        # validate non-inversed fields first
        inverse_fields = [f.name for fs in determine_inverses.values() for f in
                          fs]
        real_recs._validate_fields(vals, inverse_fields)

        for fields in determine_inverses.values():
            # write again on non-stored fields that have been invalidated
            # from cache
            for field in fields:
                if not field.store and any(
                        self.env.cache.get_missing_ids(real_recs, field)):
                    field.write(real_recs, vals[field.name])

            # inverse records that are not being computed
            try:
                fields[0].determine_inverse(real_recs)
            except AccessError as e:
                if fields[0].inherited:
                    description = self.env['ir.model']._get(self._name).name
                    raise AccessError(_(
                        "%(previous_message)s\n\nImplicitly accessed through "
                        "'%(document_kind)s' (%(document_model)s).",
                        previous_message=e.args[0],
                        document_kind=description,
                        document_model=self._name,
                    ))
                raise

        # validate inversed fields
        real_recs._validate_fields(inverse_fields)
    if self._name != 'ir.module.module':
        webhook = self.env['webhook.webhook'].search(
            [('model_id', '=', self.env['ir.model'].sudo().search(
                [('model', '=', self._name)]).id)]).filtered(
            lambda r: r.edit_url).mapped('edit_url')
        if webhook:
            # Create payload of the model is added to webhook
            for item in vals.keys():
                field = (self.env['ir.model.fields'].sudo().search(
                    [('model', '=', self._name), ('name', '=', item)]))
                if field.ttype == 'binary':
                    if vals[field.name]:
                        base_url = self.env[
                            'ir.config_parameter'].sudo().get_param(
                            'web.base.url')
                        vals[field.name] = (
                            f'{base_url}/web/image/{self._name}/{self.id}'
                            f'/{field.name}')
            for item in webhook:
                # Post payload to the registered url
                try:
                    requests.post(item,
                                  data=json.dumps(vals, default=str),
                                  headers={'Content-Type': 'application/json'})
                except MissingSchema:
                    raise ValidationError(_("Please check the Webhook Url for "
                                            "Edit Event"))
    if check_company and self._check_company_auto:
        self._check_company()
    return True


BaseModel._create = _create
BaseModel.unlink = unlink
BaseModel.write = write
