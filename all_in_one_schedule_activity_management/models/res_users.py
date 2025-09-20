# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#     Author:Adarsh K(<https://www.cybrosys.com>)
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
from odoo import _, api, models, modules
from collections import defaultdict


class Users(models.Model):
    """This class is used to create tags for activity"""
    _inherit = 'res.users'

    @api.model
    def _get_activity_groups(self):
        search_limit = int(self.env['ir.config_parameter'].sudo().get_param('mail.activity.systray.limit', 1000))
        activities = self.env["mail.activity"].search(
            [("user_id", "=", self.env.uid)], order='id desc', limit=search_limit)
        activities_by_record_by_model_name = defaultdict(lambda: defaultdict(lambda: self.env["mail.activity"]))
        for activity in activities:
            record = self.env[activity.res_model].browse(activity.res_id)
            activities_by_record_by_model_name[activity.res_model][record] += activity
        activities_by_model_name = defaultdict(lambda: self.env["mail.activity"])
        user_company_ids = self.env.user.company_ids.ids
        is_all_user_companies_allowed = set(user_company_ids) == set(self.env.context.get('allowed_company_ids') or [])
        for model_name, activities_by_record in activities_by_record_by_model_name.items():
            res_ids = [r.id for r in activities_by_record]
            Model = self.env[model_name].with_context(**self.env.context)
            has_model_access_right = self.env[model_name].check_access_rights('read', raise_exception=False)
            if has_model_access_right:
                allowed_records = Model.browse(res_ids)._filter_access_rules('read')
            else:
                allowed_records = self.env[model_name]
            unallowed_records = Model.browse(res_ids) - allowed_records
            if has_model_access_right and unallowed_records and not is_all_user_companies_allowed:
                unallowed_records -= unallowed_records.with_context(
                    allowed_company_ids=user_company_ids)._filter_access_rules('read')
            for record, activities in activities_by_record.items():
                if record in unallowed_records:
                    activities_by_model_name['mail.activity'] += activities
                elif record in allowed_records:
                    activities_by_model_name[model_name] += activities
        model_ids = [self.env["ir.model"]._get_id(name) for name in activities_by_model_name]
        user_activities = {}
        for model_name, activities in activities_by_model_name.items():
            Model = self.env[model_name]
            module = Model._original_module
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
                "view_type": getattr(Model, '_systray_view', 'list'),
            }
            if model_name == 'mail.activity':
                user_activities[model_name]['activity_ids'] = activities.ids
            for activity in activities:
                if activity.state != "cancel":
                    user_activities[model_name]["%s_count" % activity.state] += 1
                    if activity.state in ("today", "overdue"):
                        user_activities[model_name]["total_count"] += 1
        if "mail.activity" in user_activities:
            user_activities["mail.activity"]["name"] = _("Other activities")
        return list(user_activities.values())
