# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from collections import defaultdict

from odoo import api, modules, _
from odoo.addons.mail.models.res_users import Users


@api.model
def systray_get_activities(self):
    """
    Overridden, to also consider the newly added states in mail activity.
    """
    activities = self.env["mail.activity"].search(
        [("user_id", "=", self.env.uid)])
    activities_by_record_by_model_name = defaultdict(
        lambda: defaultdict(lambda: self.env["mail.activity"]))
    for activity in activities:
        record = self.env[activity.res_model].browse(activity.res_id)
        activities_by_record_by_model_name[activity.res_model][
            record] += activity
    model_ids = list({self.env["ir.model"]._get(name).id for name in
                      activities_by_record_by_model_name.keys()})
    user_activities = {}
    for model_name, activities_by_record in activities_by_record_by_model_name.items():
        domain = [
            ("id", "in", list({r.id for r in activities_by_record.keys()}))]
        allowed_records = self.env[model_name].search(domain)
        if not allowed_records:
            continue
        module = self.env[model_name]._original_module
        icon = module and modules.module.get_module_icon(module)
        model = self.env["ir.model"]._get(model_name).with_prefetch(model_ids)
        user_activities[model_name] = {
            "id": model.id,
            "name": model.name,
            "model": model_name,
            "type": "activity",
            "icon": icon,
            "total_count": 0,
            "today_count": 0,
            "overdue_count": 0,
            "planned_count": 0,
            "done_count": 0,
            "cancel_count": 0,
            "actions": [
                {
                    "icon": "fa-clock-o",
                    "name": "Summary",
                }
            ],
        }
        for record, activities in activities_by_record.items():
            if record not in allowed_records:
                continue
            for activity in activities:
                user_activities[model_name]["%s_count" % activity.state] += 1
                if activity.state in ("today", "overdue"):
                    user_activities[model_name]["total_count"] += 1
    return list(user_activities.values())


Users.systray_get_activities = systray_get_activities
