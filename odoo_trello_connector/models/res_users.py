# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Subina (odoo@cybrosys.com)
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
import requests
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    """Inherits res users for including Trello fields and functions"""
    _inherit = 'res.users'

    api_key = fields.Char(string='API KEY',
                          help="It is used to connect with Trello")
    token = fields.Char(string='Token',
                        help="The token for connecting Odoo with Trello")
    user_name = fields.Char(string='Trello Username',
                            help="The member name used in Trello")

    _sql_constraints = [
        ('api_key_uniq',
         'unique(api_key)',
         'API Key must be unique per User !'),
        ('username_uniq',
         'unique(user_name)',
         'Username must be unique per User !')
    ]

    def action_import(self):
        """Function that imports boards, lists and cards from Trello to Odoo"""
        if not self.api_key or not self.token or not self.user_name:
            raise ValidationError(_("Please fill all fields."))
        query = {
            "key": self.api_key,
            "token": self.token,
        }
        header = {
            "Accept": "application/json"
        }
        member = self.get_member_id(header, self.user_name)
        for board in self.get_boards(header, query,
                                     member):
            project = self.env['project.project'].sudo().search(
                [('trello_reference', '=', board['id'])])
            if not project:
                project = self.env['project.project'].sudo().create({
                    'name': board['name'],
                    'description': board['desc'],
                    'trello_reference': board['id']
                })
            for rec in self.get_list_on_board(header, query, board['id']):
                stages = self.env[
                    'project.task.type'].search([])
                if rec['name'] not in stages.mapped('name'):
                    self.env['project.task.type'].sudo().create({
                        'name': rec['name']
                    })
                project.sudo().write(
                    {'type_ids': [(4, stages.search([(
                        'name', '=', rec['name'])])[0].id, project.id)]})
            for card in self.get_cards(header, query,
                                       board['id']):
                if card['id'] not in self.env['project.task'].search([]).mapped(
                        'trello_reference'):
                    self.env['project.task'].create({
                        'name': card['name'],
                        'project_id': project.id,
                        'stage_id': self.env[
                            'project.task.type'].search([('name', '=',
                                                          self.get_a_list(
                                                              header, query,
                                                              card['idList'])[
                                                              'name'])])[0].id,
                        'trello_reference': card['id']
                    })

    def action_export(self):
        """Function that exports Project, Stages and Tasks from Odoo to
        Trello"""
        if not self.api_key or not self.token or not self.user_name:
            raise ValidationError(_("Please fill all fields"))
        query = {
            "key": self.api_key,
            "token": self.token,
        }
        header = {
            "Accept": "application/json"
        }
        for project in self.env['project.project'].search([]):
            if not project.trello_reference:
                board = self.create_board(header, query,
                                          project.name)
                project.write({
                    'trello_reference': board
                })
            lists_on_board = self.get_list_on_board(header,
                                                    query,
                                                    project.trello_reference)
            for stage in project.type_ids:
                if stage.name not in [rec['name'] for rec in
                                      lists_on_board]:
                    list_ref = self.create_list(header, query,
                                                project.trello_reference,
                                                stage.name)['id']
                    self.env['project.task'].search(
                        [('project_id', '=', project.id)]).filtered(
                        lambda x: x.stage_id == stage).write({
                            'stage_reference': list_ref
                        })
            for task in self.env['project.task'].search(
                    [('project_id', '=', project.id)]).filtered(
                        lambda x: x.project_id):
                for rec in lists_on_board:
                    if rec['name'] == task.stage_id.name:
                        task.write({
                            'stage_reference': rec['id']
                        })
                if not task.trello_reference:
                    card = self.create_card(header, query,
                                            task.stage_reference,
                                            task.name)
                    task.write({
                        'trello_reference': card['id']
                    })

    def get_member_id(self, headers, username):
        """Returns member id of the user"""
        response = requests.get(
            f"https://api.trello.com/1/members/{username}",
            headers=headers, timeout=10)
        print(response,'member')
        if response.status_code == 200:
            return response.json()['id']
        if response.status_code == 404:
            raise ValidationError(_('Please Check Your Credentials'))
        raise ValidationError(_(response.text.capitalize()))

    def get_boards(self, headers, query, member_id):
        """Returns details of all boards that a member belongs to"""
        query['filter'] = 'open'
        response = requests.get(
            f"https://api.trello.com/1/members/{member_id}/boards",
            headers=headers, timeout=10, params=query)
        if response.status_code == 200:
            return response.json()
        raise ValidationError(_(response.text.capitalize()))

    def get_cards(self, headers, query, board_id):
        """Returns all cards on a board"""
        response = requests.get(
            f"https://api.trello.com/1/boards/{board_id}/cards",
            headers=headers, timeout=10, params=query)
        if response.status_code == 200:
            return response.json()
        raise ValidationError(_(response.text.capitalize()))

    def get_list_on_board(self, headers, query, board_id):
        """Returns all list of a board"""
        response = requests.get(
            f"https://api.trello.com/1/boards/{board_id}/lists",
            headers=headers, timeout=10, params=query)
        if response.status_code == 200:
            return response.json()
        raise ValidationError(_(response.text.capitalize()))

    def create_board(self, headers, query, name):
        """Create new board in Trello"""
        query['name'] = {name}
        response = requests.post("https://api.trello.com/1/boards/",
                                 headers=headers, params=query,
                                 timeout=10)
        if response.status_code == 200:
            lists = requests.get(
                f"https://api.trello.com/1/boards/{response.json()['id']}/"
                f"lists",
                headers=headers, timeout=10, params=query)
            if lists.status_code == 200:
                for rec in lists.json():
                    query['closed'] = 'true'
                    requests.put(
                        f"https://api.trello.com/1/lists/{rec['id']}",
                        headers=headers, params=query, timeout=10)
            query['closed'] = 'false'
        else:
            raise ValidationError(_(response.text.capitalize()))
        return response.json()['id']

    def create_list(self, headers, query, board_id, name):
        """Create new list in Trello"""
        query['name'] = {name}
        response = requests.post(
            f"https://api.trello.com/1/boards/{board_id}/lists",
            headers=headers, timeout=10, params=query)
        if response.status_code == 200:
            return response.json()
        raise ValidationError(_(response.text.capitalize()))

    def create_card(self, headers, query, list_id, name):
        """Create new card in Trello"""
        query['idList'] = list_id
        query['name'] = {name}
        response = requests.post(
            "https://api.trello.com/1/cards", headers=headers,
            params=query, timeout=10)
        if response.status_code == 200:
            return response.json()
        raise ValidationError(_(response.text.capitalize()))

    def get_a_list(self, headers, query, list_id):
        """Method for fetching a list"""
        response = requests.get(
            f"https://api.trello.com/1/lists/{list_id}", headers=headers,
            params=query, timeout=10)
        if response.status_code == 200:
            return response.json()
        raise ValidationError(_(response.text.capitalize()))
