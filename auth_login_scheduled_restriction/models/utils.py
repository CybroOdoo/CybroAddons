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

from datetime import datetime


def convert_decimal_to_time(decimal_hour):
    """
    Convert decimal hour format to time string.
    
    Args:
        decimal_hour (float): Hour in decimal format (e.g., 9.5 for 9:30 AM)
        
    Returns:
        str: Time string in HH:MM format
    """
    if not decimal_hour:
        return ""
    
    hours = int(decimal_hour)
    minutes = int((decimal_hour - hours) * 60)
    return f"{hours:02d}:{minutes:02d}"


def convert_time_to_decimal(time_string):
    """
    Convert time string to decimal hour format.
    
    Args:
        time_string (str): Time string in HH:MM format
        
    Returns:
        float: Decimal hour format
    """
    if not time_string:
        return 0.0
    
    try:
        hours, minutes = map(int, time_string.split(':'))
        return hours + minutes / 60.0
    except (ValueError, AttributeError):
        return 0.0


def is_time_within_range(current_time, from_hour, to_hour):
    """
    Check if current time is within the given range.
    
    Args:
        current_time (datetime): Current datetime
        from_hour (float): Start hour in decimal format
        to_hour (float): End hour in decimal format
        
    Returns:
        bool: True if current time is within range
    """
    if not from_hour or not to_hour:
        return False
    
    current_decimal = current_time.hour + current_time.minute / 60.0
    return from_hour <= current_decimal <= to_hour


def get_current_decimal_hour():
    """
    Get current time in decimal hour format.
    
    Returns:
        float: Current time as decimal hour
    """
    now = datetime.now()
    return now.hour + now.minute / 60.0


def get_day_name(day_of_week):
    """
    Get day name from day of week number.
    
    Args:
        day_of_week (int): 0=Monday, 1=Tuesday, ..., 6=Sunday
        
    Returns:
        str: Day name
    """
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 
            'Friday', 'Saturday', 'Sunday']
    return days[day_of_week] if 0 <= day_of_week <= 6 else ""

