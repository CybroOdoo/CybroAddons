# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nilmar Shereef(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api


class TaskFollow(models.Model):
    _inherit = 'project.task'

    @api.multi
    def message_auto_subscribe(self, updated_fields, values=None):

        """ override 'message_auto_subscribe' function in 'mail.thread' ."""

        new_partners, new_channels = dict(), dict()
        restrict_task_follow = self.project_id.restrict_automatic_task_follow
        user_field_lst = self._message_get_auto_subscribe_fields(updated_fields)
        subtypes = self.env['mail.message.subtype'].search(
            ['|', ('res_model', '=', False), ('parent_id.res_model', '=', self._name)])
        relation_fields = set([subtype.relation_field for subtype in subtypes if subtype.relation_field is not False])
        if not any(relation in updated_fields for relation in relation_fields) and not user_field_lst:
            return True
        if values is None:
            record = self[0]
            for updated_field in updated_fields:
                field_value = getattr(record, updated_field)
                if isinstance(field_value, models.BaseModel):
                    field_value = field_value.id
                values[updated_field] = field_value
        headers = set()
        for subtype in subtypes:
            if subtype.relation_field and values.get(subtype.relation_field):
                headers.add((subtype.res_model, values.get(subtype.relation_field)))
        if headers:
            header_domain = ['|'] * (len(headers) - 1)
            for header in headers:
                header_domain += ['&', ('res_model', '=', header[0]), ('res_id', '=', header[1])]
            if not restrict_task_follow:
                for header_follower in self.env['mail.followers'].sudo().search(header_domain):
                    for subtype in header_follower.subtype_ids:
                        if subtype.parent_id and subtype.parent_id.res_model == self._name:
                            new_subtype = subtype.parent_id
                        elif subtype.res_model is False:
                            new_subtype = subtype
                        else:
                            continue
                        if header_follower.partner_id:
                            new_partners.setdefault(header_follower.partner_id.id, set()).add(new_subtype.id)
                        else:
                            new_channels.setdefault(header_follower.channel_id.id, set()).add(new_subtype.id)
        user_ids = [values[name] for name in user_field_lst if values.get(name)]
        user_pids = [user.partner_id.id for user in self.env['res.users'].sudo().browse(user_ids)]
        for partner_id in user_pids:
            new_partners.setdefault(partner_id, None)
        for pid, subtypes in new_partners.items():
            subtypes = list(subtypes) if subtypes is not None else None
            self.message_subscribe(partner_ids=[pid], subtype_ids=subtypes, force=(subtypes != None))
        for cid, subtypes in new_channels.items():
            subtypes = list(subtypes) if subtypes is not None else None
            self.message_subscribe(channel_ids=[cid], subtype_ids=subtypes, force=(subtypes != None))
        user_pids = [user_pid for user_pid in user_pids if user_pid != self.env.user.partner_id.id]
        self._message_auto_subscribe_notify(user_pids)
        return True


class ProjectFollow(models.Model):
    _inherit = 'project.project'

    restrict_automatic_task_follow = fields.Boolean(string="Disable Automatic Task Following",
                                                    help="It will remove unwanted project followers on task."
                                                         "Only assigned person & created person will follow this task automatically.")
