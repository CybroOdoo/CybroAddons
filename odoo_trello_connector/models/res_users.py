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
import requests

from odoo import fields, models
from odoo.exceptions import ValidationError

TRELLO_API = "https://api.trello.com/1"
TIMEOUT = 10


class ResUsers(models.Model):
    """Inherits res users for including Trello fields and functions"""
    _inherit = 'res.users'

    api_key = fields.Char(string='API Key',
                          help="It is used to connect with Trello")
    token = fields.Char(help="The token for connecting Odoo with Trello")
    user_name = fields.Char(string='Trello Username',
                            help="The member name used in Trello")

    _api_key_uniq = models.Constraint(
        'unique(api_key)',
        'API Key must be unique per user!',
    )
    _username_uniq = models.Constraint(
        'unique(user_name)',
        'Trello Username must be unique per user!',
    )

    def _get_trello_auth(self):
        """Validate the credentials and return the request parameters"""
        self.ensure_one()
        if not self.api_key or not self.token or not self.user_name:
            raise ValidationError(self.env._("Please fill in all fields."))
        return {"key": self.api_key, "token": self.token}

    def _notify_success(self, message):
        """Return a success notification action"""
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': self.env._('Success'),
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }

    def _raise_trello_error(self, response):
        """Raise a validation error with the response of Trello"""
        raise ValidationError(response.text.capitalize())

    def action_import(self):
        """Function that imports boards, lists and cards from Trello to Odoo"""
        query = self._get_trello_auth()
        header = {"Accept": "application/json"}
        member = self.get_member_id(header, self.user_name)
        for board in self.get_boards(header, query, member):
            self.with_delay(
                channel='root.import_project',
                description='Importing Board From Trello',
                max_retries=10)._delay_import(board, header, query)
        return self._notify_success(
            self.env._('Import completed successfully.'))

    def _delay_import(self, board, header, query):
        """Import will be performed within the job queue"""
        project_model = self.env['project.project'].sudo()
        stage_model = self.env['project.task.type'].sudo()
        task_model = self.env['project.task']
        project = project_model.search(
            [('trello_reference', '=', board['id'])], limit=1)
        if not project:
            project = project_model.create({
                'name': board['name'],
                'description': board['desc'],
                'trello_reference': board['id'],
            })
        for rec in self.get_list_on_board(header, query, board['id']):
            stage = stage_model.search([('name', '=', rec['name'])], limit=1)
            if not stage:
                stage = stage_model.create({'name': rec['name']})
            project.write({'type_ids': [(4, stage.id)]})
        for card in self.get_cards(header, query, board['id']):
            if task_model.search_count(
                    [('trello_reference', '=', card['id'])]):
                continue
            list_name = self.get_a_list(header, query, card['idList'])['name']
            stage = stage_model.search([('name', '=', list_name)], limit=1)
            task_model.create({
                'name': card['name'],
                'project_id': project.id,
                'stage_id': stage.id,
                'trello_reference': card['id'],
            })

    def action_export(self):
        """Function that exports Project, Stages and Tasks from Odoo to
        Trello"""
        query = self._get_trello_auth()
        header = {"Accept": "application/json"}
        # checking username exist or not
        self.get_member_id(header, self.user_name)
        for project in self.env['project.project'].search(
                [('active', '=', True)]):
            if not project.trello_reference:
                project.write({
                    'trello_reference': self.create_board(
                        header, query, project.name)
                })
            lists_on_board = self.get_list_on_board(
                header, query, project.trello_reference)
            # Ensure all stages exist on Trello
            for stage in project.type_ids.sorted(
                    key=lambda s: s.sequence, reverse=True):
                if stage.name not in [rec['name'] for rec in lists_on_board]:
                    list_ref = self.create_list(
                        header, query, project.trello_reference,
                        stage.name)['id']
                    lists_on_board.append({'name': stage.name, 'id': list_ref})
            # Sync tasks
            for task in self.env['project.task'].search(
                    [('project_id', '=', project.id)]):
                old_stage_ref = task.stage_reference
                # Find the matching Trello list for the current task stage
                trello_list_id = next(
                    (rec['id'] for rec in lists_on_board
                     if rec['name'] == task.stage_id.name), None)
                if trello_list_id and task.stage_reference != trello_list_id:
                    task.write({'stage_reference': trello_list_id})
                if task.trello_reference:
                    # Move card if stage changed
                    if old_stage_ref and task.stage_reference != old_stage_ref:
                        requests.put(
                            f"{TRELLO_API}/cards/{task.trello_reference}",
                            headers=header,
                            params=dict(query, idList=task.stage_reference),
                            timeout=TIMEOUT)
                elif task.stage_reference:
                    # Create new card if it doesn't exist on Trello
                    card = self.create_card(
                        header, query, task.stage_reference, task.name)
                    task.write({'trello_reference': card['id']})
        return self._notify_success(
            self.env._('Export completed successfully.'))

    def get_member_id(self, headers, username):
        """Returns member id of the user"""
        response = requests.get(
            f"{TRELLO_API}/members/{username}", headers=headers,
            params={"key": self.api_key, "token": self.token},
            timeout=TIMEOUT)
        if response.status_code == 200:
            return response.json()['id']
        if response.status_code in (401, 404):
            raise ValidationError(self.env._('Please check your credentials.'))
        self._raise_trello_error(response)

    def get_boards(self, headers, query, member_id):
        """Returns details of all boards that a member belongs to"""
        response = requests.get(
            f"{TRELLO_API}/members/{member_id}/boards", headers=headers,
            params=dict(query, filter='open'), timeout=TIMEOUT)
        if response.status_code == 200:
            return response.json()
        self._raise_trello_error(response)

    def get_cards(self, headers, query, board_id):
        """Returns all cards on a board"""
        response = requests.get(
            f"{TRELLO_API}/boards/{board_id}/cards", headers=headers,
            params=query, timeout=TIMEOUT)
        if response.status_code == 200:
            return response.json()
        self._raise_trello_error(response)

    def get_list_on_board(self, headers, query, board_id):
        """Returns all lists of a board"""
        response = requests.get(
            f"{TRELLO_API}/boards/{board_id}/lists", headers=headers,
            params=query, timeout=TIMEOUT)
        if response.status_code == 200:
            return response.json()
        self._raise_trello_error(response)

    def create_board(self, headers, query, name):
        """Create new board in Trello and close its default lists"""
        response = requests.post(
            f"{TRELLO_API}/boards/", headers=headers,
            params=dict(query, name=name), timeout=TIMEOUT)
        if response.status_code != 200:
            self._raise_trello_error(response)
        board_id = response.json()['id']
        lists = requests.get(
            f"{TRELLO_API}/boards/{board_id}/lists", headers=headers,
            params=query, timeout=TIMEOUT)
        if lists.status_code == 200:
            for rec in lists.json():
                requests.put(
                    f"{TRELLO_API}/lists/{rec['id']}", headers=headers,
                    params=dict(query, closed='true'), timeout=TIMEOUT)
        return board_id

    def create_list(self, headers, query, board_id, name):
        """Create new list in Trello"""
        response = requests.post(
            f"{TRELLO_API}/boards/{board_id}/lists", headers=headers,
            params=dict(query, name=name), timeout=TIMEOUT)
        if response.status_code == 200:
            return response.json()
        self._raise_trello_error(response)

    def create_card(self, headers, query, list_id, name):
        """Create new card in Trello"""
        response = requests.post(
            f"{TRELLO_API}/cards", headers=headers,
            params=dict(query, idList=list_id, name=name), timeout=TIMEOUT)
        if response.status_code == 200:
            return response.json()
        self._raise_trello_error(response)

    def get_a_list(self, headers, query, list_id):
        """Method for fetching a list"""
        response = requests.get(
            f"{TRELLO_API}/lists/{list_id}", headers=headers,
            params=query, timeout=TIMEOUT)
        if response.status_code == 200:
            return response.json()
        self._raise_trello_error(response)
