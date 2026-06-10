# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import fields, models


class LoginRestrictionConfig(models.Model):
    """Model to manage login restrictions based on working hours."""
    _name = 'login.restriction.config'
    _description = 'Login Restriction Configuration'
    _rec_name = 'user_id'

    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        ondelete='cascade',
        help='Select the user to apply login restrictions'
    )
    is_restricted = fields.Boolean(
        string='Enable Login Restriction',
        default=False,
        help='Enable time-based login restrictions for this user'
    )
    monday_from = fields.Float(
        string='Monday From',
        help='Start time in hours (e.g., 9.0 for 9:00 AM)'
    )
    monday_to = fields.Float(
        string='Monday To',
        help='End time in hours (e.g., 17.0 for 5:00 PM)'
    )
    tuesday_from = fields.Float(string='Tuesday From')
    tuesday_to = fields.Float(string='Tuesday To')
    wednesday_from = fields.Float(string='Wednesday From')
    wednesday_to = fields.Float(string='Wednesday To')
    thursday_from = fields.Float(string='Thursday From')
    thursday_to = fields.Float(string='Thursday To')
    friday_from = fields.Float(string='Friday From')
    friday_to = fields.Float(string='Friday To')
    saturday_from = fields.Float(string='Saturday From')
    saturday_to = fields.Float(string='Saturday To')
    sunday_from = fields.Float(string='Sunday From')
    sunday_to = fields.Float(string='Sunday To')
    allow_admin_bypass = fields.Boolean(
        string='Allow Admin Bypass',
        default=True,
        help='Allow administrators to bypass login restrictions'
    )
    error_message = fields.Text(
        string='Restriction Error Message',
        default='Login is restricted outside working hours.',
        help='Message shown when user tries to login outside working hours'
    )

    _sql_constraints = [
        ('unique_user_restriction', 'unique(user_id)', 
         'A restriction configuration already exists for this user.')
    ]

    def get_working_hours(self, day_of_week):
        """
        Get working hours for a specific day.
        
        Args:
            day_of_week (int): 0=Monday, 1=Tuesday, ..., 6=Sunday
            
        Returns:
            tuple: (from_hour, to_hour) or (None, None) if no working hours
        """
        day_mapping = {
            0: ('monday_from', 'monday_to'),
            1: ('tuesday_from', 'tuesday_to'),
            2: ('wednesday_from', 'wednesday_to'),
            3: ('thursday_from', 'thursday_to'),
            4: ('friday_from', 'friday_to'),
            5: ('saturday_from', 'saturday_to'),
            6: ('sunday_from', 'sunday_to'),
        }
        
        from_field, to_field = day_mapping.get(day_of_week, (None, None))
        if from_field and to_field:
            from_hour = getattr(self, from_field, 0.0)
            to_hour = getattr(self, to_field, 0.0)
            if from_hour and to_hour:
                return (from_hour, to_hour)
        return (None, None)

    def is_within_working_hours(self):
        """Check if current time is within working hours."""
        from datetime import datetime
        import pytz
        
        if not self.is_restricted:
            return True
        
        now_utc = datetime.utcnow()
        # Ensure we default to IST for Cybrosys environments when user profile has no configured timezone
        tz_name = self.user_id.tz or self.env.context.get('tz') or 'Asia/Kolkata'
        try:
            user_tz = pytz.timezone(tz_name)
        except Exception:
            user_tz = pytz.UTC
            
        now_local = pytz.utc.localize(now_utc).astimezone(user_tz)
        
        day_of_week = now_local.weekday()
        current_hour = now_local.hour + now_local.minute / 60.0
        
        from_hour, to_hour = self.get_working_hours(day_of_week)
        
        if from_hour is None or to_hour is None:
            # No working hours defined for this day
            return False
            
        def convert_float_to_time(time_float):
            """Convert float like 9.30 (meaning 9:30) to decimal hours (9.5)"""
            hour = int(time_float)
            minute = round((time_float - hour) * 100)
            return hour + (minute / 60.0)
            
        from_time = convert_float_to_time(from_hour)
        to_time = convert_float_to_time(to_hour)
        
        return from_time <= current_hour <= to_time

