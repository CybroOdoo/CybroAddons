# -*- coding: utf-8 -*-
################################################################################
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
################################################################################
from odoo import Command, fields, models
from odoo.exceptions import UserError

PAGE_SIZE = 50
ITEM_PAGE_SIZE = 100
CONTACT_BOARD_NAME = 'contacts'

ITEM_FIELDS = 'id name group { id } column_values { id type text }'
BOARDS_QUERY = (
    'query ($page: Int!, $limit: Int!) { boards(limit: $limit, page: $page) '
    '{ id name description owner { name } columns { id title type } '
    'groups { id title } } }')
ITEMS_QUERY = (
    'query ($board_ids: [ID!], $limit: Int!) { boards(ids: $board_ids) '
    '{ items_page(limit: $limit) { cursor items { %s } } } }' % ITEM_FIELDS)
NEXT_ITEMS_QUERY = (
    'query ($cursor: String!, $limit: Int!) { next_items_page('
    'limit: $limit, cursor: $cursor) { cursor items { %s } } }' % ITEM_FIELDS)
USERS_QUERY = (
    'query ($page: Int!, $limit: Int!) { users(limit: $limit, page: $page) '
    '{ id name email } }')


class MondayConnector(models.TransientModel):
    _name = 'monday.connector'
    _description = 'Monday Connector'
    _rec_name = 'credential_id'

    credential_id = fields.Many2one('monday.credential',
                                    required=True,
                                    string="Monday Credentials",
                                    help="Select the credential for connecting"
                                         " with Monday.com")
    import_user = fields.Boolean(help="Check if you want to import user")
    import_board = fields.Boolean(help="Check if you want to import board, "
                                       "its groups and its items")
    import_contact = fields.Boolean(string="Import Customer",
                                    help="Check if you want to import the "
                                         "items of the Contacts board as "
                                         "customers")

    def action_execute(self):
        """Import the selected data from Monday.com to Odoo."""
        self.ensure_one()
        if not (self.import_user or self.import_board):
            raise UserError(self.env._(
                "Please select at least one kind of data to import."))
        counts = {'boards': 0, 'items': 0, 'customers': 0, 'users': 0}
        if self.import_board:
            self._import_boards(counts)
        if self.import_user:
            self._import_users(counts)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': self.env._("Import Completed"),
                'message': self.env._(
                    "Boards: %(boards)s, Items: %(items)s, "
                    "New customers: %(customers)s, New users: %(users)s.",
                    **counts),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }

    def _fetch_pages(self, query, key):
        """Return all the records of a page-based Monday.com query."""
        records = []
        page = 1
        while True:
            data = self.credential_id._monday_request(
                query, {'page': page, 'limit': PAGE_SIZE})
            batch = data.get(key) or []
            records.extend(batch)
            if len(batch) < PAGE_SIZE:
                return records
            page += 1

    def _fetch_items(self, board_reference):
        """Return all the items of a board, following the cursor."""
        credential = self.credential_id
        data = credential._monday_request(
            ITEMS_QUERY,
            {'board_ids': [board_reference], 'limit': ITEM_PAGE_SIZE})
        boards = data.get('boards') or []
        page = (boards[0].get('items_page') if boards else None) or {}
        items = []
        while True:
            items.extend(page.get('items') or [])
            cursor = page.get('cursor')
            if not cursor:
                return items
            data = credential._monday_request(
                NEXT_ITEMS_QUERY,
                {'cursor': cursor, 'limit': ITEM_PAGE_SIZE})
            page = data.get('next_items_page') or {}

    def _import_boards(self, counts):
        """Import (create or update) boards, groups, items and customers
        from Monday.com."""
        Board = self.env['monday.board']
        for rec in self._fetch_pages(BOARDS_QUERY, 'boards'):
            vals = {
                'name': rec.get('name'),
                'owner': (rec.get('owner') or {}).get('name') or False,
                'description': rec.get('description') or False,
            }
            board = Board.search(
                [('board_reference', '=', rec['id'])], limit=1)
            if board:
                board.write(vals)
            else:
                board = Board.create(
                    dict(vals, board_reference=rec['id']))
            counts['boards'] += 1
            groups = self._import_groups(board, rec.get('groups') or [])
            titles = {column['id']: column['title']
                      for column in rec.get('columns') or []}
            items = self._fetch_items(rec['id'])
            self._import_items(board, items, groups, titles)
            counts['items'] += len(items)
            if self.import_contact and (
                    (rec.get('name') or '').strip().lower()
                    == CONTACT_BOARD_NAME):
                counts['customers'] += self._import_contacts(
                    items, rec.get('columns') or [])

    def _import_groups(self, board, group_data):
        """Create or update the groups of a board and return them by id."""
        groups = {group.group: group for group in board.group_ids}
        for rec in group_data:
            group = groups.get(rec['id'])
            if group:
                if group.name != rec['title']:
                    group.name = rec['title']
            else:
                groups[rec['id']] = self.env['monday.group'].create({
                    'name': rec['title'],
                    'group': rec['id'],
                    'board_id': board.id,
                })
        return groups

    def _import_items(self, board, items, groups, titles):
        """Create or update the items of a board by their Monday.com id."""
        Item = self.env['monday.item']
        existing = {item.item_reference: item for item in board.item_ids
                    if item.item_reference}
        # Items imported by an older version have no reference: match by name
        legacy = {item.name: item for item in board.item_ids
                  if not item.item_reference}
        for rec in items:
            group = groups.get((rec.get('group') or {}).get('id'))
            column_values = [Command.create({
                'column_reference': value['id'],
                'title': titles.get(value['id'], value['id']),
                'text': value.get('text') or False,
            }) for value in rec.get('column_values') or []]
            vals = {
                'name': rec['name'],
                'group_id': group.id if group else False,
                'item_reference': rec['id'],
            }
            item = existing.get(rec['id']) or legacy.get(rec['name'])
            if item:
                item.write(dict(vals, column_value_ids=[Command.clear()]
                                + column_values))
            else:
                Item.create(dict(vals, board_id=board.id,
                                 column_value_ids=column_values))

    def _import_contacts(self, items, columns):
        """Create the customers of the Contacts board which are not yet in
        Odoo and return the number of created customers."""
        Partner = self.env['res.partner']
        email_ids = {c['id'] for c in columns if c.get('type') == 'email'}
        email_ids.add('contact_email')
        phone_ids = {c['id'] for c in columns if c.get('type') == 'phone'}
        phone_ids.add('contact_phone')
        created = 0
        for item in items:
            values = {value['id']: (value.get('text') or '').strip()
                      for value in item.get('column_values') or []}
            email = next((values[key] for key in email_ids
                          if values.get(key)), '')
            phone = next((values[key] for key in phone_ids
                          if values.get(key)), '')
            if email:
                domain = [('email', '=', email)]
            else:
                domain = [('name', '=', item['name']),
                          ('monday_reference', '=', True)]
            if Partner.search(domain, limit=1):
                continue
            Partner.create({
                'name': item['name'],
                'phone': phone or False,
                'email': email or False,
                'monday_reference': True,
            })
            created += 1
        return created

    def _import_users(self, counts):
        """Create the Monday.com users which do not exist in Odoo.

        The users are created as portal users without any password: they
        do not use an internal license and have to use the reset password
        flow to be able to log in."""
        Users = self.env['res.users'].with_context(active_test=False)
        portal_group = self.env.ref('base.group_portal')
        for rec in self._fetch_pages(USERS_QUERY, 'users'):
            email = (rec.get('email') or '').strip()
            if not email:
                continue
            if Users.search(['|', ('login', '=', email),
                             ('monday_reference', '=', rec['id'])], limit=1):
                continue
            Users.create({
                'name': rec['name'],
                'email': email,
                'login': email,
                'group_ids': [Command.set(portal_group.ids)],
                'monday_reference': rec['id'],
            })
            counts['users'] += 1
