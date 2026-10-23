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
from odoo import Command
from . import models


def _post_init_hook(env):
    """Assign existing internal users to chatter access groups on install."""
    group_send = env.ref('mail_message_access.group_allow_send_message_btn', raise_if_not_found=False)
    group_log = env.ref('mail_message_access.group_allow_log_note_btn', raise_if_not_found=False)
    internal_users = env['res.users'].search([('share', '=', False)])
    if internal_users:
        user_commands = [Command.link(u.id) for u in internal_users]
        if group_send:
            group_send.write({'user_ids': user_commands})
        if group_log:
            group_log.write({'user_ids': user_commands})
