# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
import time as time_module
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, date, time as dt_time
import pytz
import requests
from requests.auth import HTTPDigestAuth
from odoo import _, api, exceptions, fields, models
from odoo.exceptions import UserError, ValidationError


class HikvisionDevice(models.Model):
    """Model for managing Hikvision biometric devices."""

    _name = 'hikvision.device'
    _inherit = ['mail.thread']
    _description = 'Hikvision Biometric Device'

    name = fields.Char(help='Name of the Biometric Device', required=True)
    ip_address = fields.Char("Device IP", help='The IP address of the Device', required=True)
    username = fields.Char("Username", help="Username of the device", required=True)
    password = fields.Char("Password", help="Password of the device", required=True)
    image = fields.Image()
    device_name = fields.Char("Device Name", help='Name of the Device')
    device_id = fields.Char("Device Id", help="Id of the the device")
    device_model = fields.Char("Model", help="Model of the device")
    device_serial_no = fields.Char("Serial No", help="Serial No of the device")
    device_mac_address = fields.Char(string='Device Mac ID', help='Mac ID of the Device')

    def _get_api_config(self, endpoint=""):
        """Get API configuration for device requests."""
        url = f"http://{self.ip_address}{endpoint}"
        auth = HTTPDigestAuth(self.username, self.password)
        headers = {"Content-Type": "application/json"}
        return url, auth, headers

    def test_connection(self):
        """Test connection and fetch device details."""
        for device in self:
            url = f"http://{device.ip_address}/ISAPI/System/deviceInfo"
            try:
                response = requests.get(url, auth=HTTPDigestAuth(device.username, device.password))
                if response.status_code == 200:
                    root = ET.fromstring(response.content)
                    ns_uri = root.tag[root.tag.find("{") + 1:root.tag.find("}")]
                    ns = {'ns': ns_uri}
                    device.device_name = root.findtext('ns:deviceName', namespaces=ns)
                    device.device_id = root.findtext('ns:deviceID', namespaces=ns)
                    device.device_model = root.findtext('ns:model', namespaces=ns)
                    device.device_serial_no = root.findtext('ns:serialNumber', namespaces=ns)
                    device.device_mac_address = root.findtext('ns:macAddress', namespaces=ns)
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': 'Successfully Connected',
                            'type': 'success',
                            'sticky': False
                        }
                    }
            except Exception as error:
                raise ValidationError(f'{error}')

    def fetch_attendance(self, start_date=None, end_date=None):
        """Fetch attendance events within date range."""
        if not self.ip_address:
            raise exceptions.UserError("Device IP address is not configured.")
        if not self.username or not self.password:
            raise exceptions.UserError("Device credentials are not configured.")

        user_tz = self.env.user.tz or "UTC"
        local_tz = pytz.timezone(user_tz)

        if not start_date or not end_date:
            today = datetime.now(local_tz).date()
            start_date = today
            end_date = today

        start_datetime = local_tz.localize(datetime.combine(start_date, dt_time.min))
        end_datetime = local_tz.localize(datetime.combine(end_date, dt_time.max))

        start_utc = start_datetime.astimezone(pytz.UTC)
        end_utc = end_datetime.astimezone(pytz.UTC)

        url, auth, headers = self._get_api_config("/ISAPI/AccessControl/AcsEvent?format=json")

        payload_template = {
            "AcsEventCond": {
                "searchID": "1",
                "searchResultPosition": 0,
                "maxResults": 30,
                "major": 5,
                "minor": 0,
                "startTime": start_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "endTime": end_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        }

        all_events = []
        position = 0
        total_matches = None

        while True:
            payload_template["AcsEventCond"]["searchResultPosition"] = position
            try:
                response = requests.post(url, auth=auth, json=payload_template, headers=headers, timeout=10)
                response.raise_for_status()
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    raise exceptions.UserError(f"Invalid JSON response from device: {response.text}")

                events = data.get('AcsEvent', {}).get('InfoList', [])
                if total_matches is None:
                    total_matches = data.get('AcsEvent', {}).get('totalMatches', 0)

                if not events:
                    break

                all_events.extend(events)

                if len(events) < payload_template["AcsEventCond"]["maxResults"]:
                    break

                position += payload_template["AcsEventCond"]["maxResults"]

                if total_matches and len(all_events) >= total_matches:
                    break

            except requests.exceptions.ConnectionError as e:
                raise exceptions.UserError(f"Failed to connect to the device at {self.ip_address}: {str(e)}")
            except requests.exceptions.HTTPError as e:
                raise exceptions.UserError(f"HTTP error occurred: {str(e)}")
            except requests.exceptions.RequestException as e:
                raise exceptions.UserError(f"Error communicating with the device: {str(e)}")

        return all_events

    def fetch_all_attendance(self):
        """Fetch all attendance events without date restrictions."""
        if not self.ip_address:
            raise exceptions.UserError("Device IP address is not configured.")
        if not self.username or not self.password:
            raise exceptions.UserError("Device credentials are not configured.")

        now = datetime.now(pytz.UTC)
        start_date = now - timedelta(days=730)
        end_date = now + timedelta(days=30)

        all_events = []
        current_date = start_date

        job = self.env.context.get('job')
        total_chunks = 0
        tmp = start_date
        while tmp < end_date:
            total_chunks += 1
            tmp = min(tmp + timedelta(days=3), end_date)
        processed_chunks = 0

        while current_date < end_date:
            chunk_end = min(current_date + timedelta(days=3), end_date)

            try:
                chunk_events = self._fetch_attendance_chunk(current_date, chunk_end)
                all_events.extend(chunk_events)
                processed_chunks += 1

                if job:
                    try:
                        if hasattr(job, 'set_progress'):
                            job.set_progress(processed_chunks, total=total_chunks)
                        elif hasattr(job, 'progress'):
                            job.progress = min(100, int(processed_chunks * 100 / total_chunks))
                    except Exception:
                        pass

                time_module.sleep(0.5)

            except Exception:
                continue

            current_date = chunk_end

        return all_events

    def _fetch_attendance_chunk(self, start_date, end_date):
        """Fetch attendance for a date range chunk."""
        url, auth, headers = self._get_api_config("/ISAPI/AccessControl/AcsEvent?format=json")

        payload_template = {
            "AcsEventCond": {
                "searchID": "1",
                "searchResultPosition": 0,
                "maxResults": 100,
                "major": 5,
                "minor": 0,
                "startTime": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "endTime": end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        }

        chunk_events = []
        position = 0
        total_matches = None

        while True:
            payload_template["AcsEventCond"]["searchResultPosition"] = position
            try:
                response = requests.post(url, auth=auth, json=payload_template, headers=headers, timeout=30)
                try:
                    response.raise_for_status()
                except requests.exceptions.HTTPError as e:
                    if response.status_code == 401:
                        try:
                            test_url, test_auth, _ = self._get_api_config("/ISAPI/System/deviceInfo")
                            requests.get(test_url, auth=test_auth, timeout=10)
                        except Exception:
                            pass
                        response = requests.post(url, auth=auth, json=payload_template, headers=headers, timeout=30)
                        response.raise_for_status()
                    else:
                        raise
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    raise exceptions.UserError(f"Invalid JSON response from device: {response.text}")

                events = data.get('AcsEvent', {}).get('InfoList', [])
                if total_matches is None:
                    total_matches = data.get('AcsEvent', {}).get('totalMatches', 0)

                if not events:
                    break

                chunk_events.extend(events)

                if len(events) < payload_template["AcsEventCond"]["maxResults"]:
                    break

                position += payload_template["AcsEventCond"]["maxResults"]

                if total_matches and len(chunk_events) >= total_matches:
                    break

            except requests.exceptions.ConnectionError as e:
                raise exceptions.UserError(f"Failed to connect to the device at {self.ip_address}: {str(e)}")
            except requests.exceptions.HTTPError as e:
                raise exceptions.UserError(f"HTTP error occurred: {str(e)}")
            except requests.exceptions.Timeout as e:
                raise exceptions.UserError(f"Request timed out: {str(e)}")
            except requests.exceptions.RequestException as e:
                raise exceptions.UserError(f"Error communicating with the device: {str(e)}")

        return chunk_events

    def fetch_and_create_attendance(self):
        """Queue job to download and create attendance records."""
        self.ensure_one()

        self.with_delay(
            description=f"Download Attendance from {self.name} ({self.ip_address})",
            priority=5,
            max_retries=3,
        ).job_download_attendance(self.id)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Job Queued'),
                'message': _(
                    'Attendance download job has been queued. You can monitor its progress in the Job Queue menu.'),
                'type': 'info',
                'sticky': False
            }
        }

    def download_all_attendance(self):
        """Queue job to download all attendance records."""
        self.ensure_one()

        self.with_delay(
            description=f"Download All Attendance from {self.name} ({self.ip_address})",
            priority=5,
            max_retries=3,
        ).job_download_all_attendance(self.id)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Job Queued'),
                'message': _(
                    'All attendance download job has been queued. This may take some time as it downloads all records. You can monitor its progress in the Job Queue menu.'),
                'type': 'info',
                'sticky': False
            }
        }

    def job_download_attendance(self, device_id, start_date=None, end_date=None):
        """Job to download and create attendance records."""
        device = self.env['hikvision.device'].browse(device_id)
        if not device.exists():
            raise exceptions.UserError(f"Device with ID {device_id} not found")

        try:
            events = device.fetch_attendance(start_date=start_date, end_date=end_date)
            employees = device.fetch_employees()

            processed_count = 0
            skipped_count = 0
            job = self.env.context.get('job')
            total_events = len(events)

            for event in events:
                processed_count += 1
                if job:
                    try:
                        job.set_progress(processed_count, total=total_events)
                    except Exception:
                        pass
                emp_no = event.get("employeeNoString")
                pass_time_str = event.get("time")
                attendance_status = event.get("attendanceStatus")

                if not emp_no or not pass_time_str or attendance_status is None:
                    continue

                employee = self.env["hr.employee"].search(
                    [("hikvision_number", "=", emp_no)], limit=1
                )
                if not employee:
                    continue

                try:
                    pass_time = datetime.strptime(pass_time_str, "%Y-%m-%dT%H:%M:%S%z")
                    pass_time = pass_time.astimezone(pytz.UTC).replace(tzinfo=None)
                except ValueError:
                    continue

                if pass_time < employee.create_date.replace(tzinfo=None):
                    skipped_count += 1
                    continue

                if attendance_status == "checkIn":
                    same_day_attendance = self.env["hr.attendance"].search([
                        ("employee_id", "=", employee.id),
                        ("check_in", ">=", pass_time.replace(hour=0, minute=0, second=0, microsecond=0)),
                        ("check_in", "<=", pass_time.replace(hour=23, minute=59, second=59, microsecond=999999)),
                    ], order="check_in desc", limit=1)

                    last_attendance = self.env["hr.attendance"].search(
                        [("employee_id", "=", employee.id)],
                        order="check_in desc",
                        limit=1,
                    )

                    if same_day_attendance and not same_day_attendance.check_out:
                        skipped_count += 1
                        continue

                    if same_day_attendance and same_day_attendance.check_out:
                        if pass_time > same_day_attendance.check_out:
                            self.env["hr.attendance"].sudo().create({
                                "employee_id": employee.id,
                                "check_in": pass_time,
                            })
                            continue
                        else:
                            continue

                    user_tz = self.env.user.tz or "UTC"
                    local_tz = pytz.timezone(user_tz)

                    if last_attendance and not last_attendance.check_out:
                        checkin_date_local = last_attendance.check_in.astimezone(local_tz).date()
                        end_of_day_local = datetime.combine(checkin_date_local, dt_time(23, 59, 59))
                        end_of_day_local = local_tz.localize(end_of_day_local)
                        end_of_day_utc = end_of_day_local.astimezone(pytz.UTC).replace(tzinfo=None)

                        last_attendance.sudo().write({"check_out": end_of_day_utc})
                        self.env.invalidate_all()

                    if last_attendance and not last_attendance.check_out and pass_time > last_attendance.check_in:
                        safe_checkout = pass_time - timedelta(seconds=1)
                        last_attendance.sudo().write({"check_out": safe_checkout})

                    try:
                        self.env["hr.attendance"].sudo().create({
                            "employee_id": employee.id,
                            "check_in": pass_time,
                        })
                    except ValidationError:
                        open_att = self.env["hr.attendance"].search([
                            ("employee_id", "=", employee.id),
                            ("check_out", "=", False)
                        ], order="check_in desc", limit=1)
                        if open_att and pass_time > open_att.check_in:
                            open_att.sudo().write({"check_out": pass_time - timedelta(seconds=1)})
                            self.env["hr.attendance"].sudo().create({
                                "employee_id": employee.id,
                                "check_in": pass_time,
                            })
                        else:
                            raise

                elif attendance_status == "checkOut":
                    last_attendance = self.env["hr.attendance"].search([
                        ("employee_id", "=", employee.id),
                    ], order="check_in desc", limit=1)

                    if last_attendance:
                        if not last_attendance.check_out:
                            if pass_time > last_attendance.check_in:
                                last_attendance.sudo().write({"check_out": pass_time})
                            else:
                                skipped_count += 1
                        else:
                            skipped_count += 1
                    else:
                        self.env["hr.attendance"].sudo().create({
                            "employee_id": employee.id,
                            "check_in": pass_time,
                            "check_out": pass_time + timedelta(seconds=1),
                        })

            return "Attendance download completed successfully"

        except Exception as e:
            raise e

    def job_download_all_attendance(self, device_id):
        """Job to download all attendance records."""
        device = self.env['hikvision.device'].browse(device_id)
        if not device.exists():
            raise exceptions.UserError(f"Device with ID {device_id} not found")

        try:
            device.test_connection()
            events = device.fetch_all_attendance()

            device.fetch_employees()
            self.env.cr.commit()

            employees = self.env["hr.employee"].search([("hikvision_number", "!=", False)])

            processed_count = 0
            skipped_count = 0
            created_count = 0
            updated_count = 0

            chunk_size = 50
            total_chunks = (len(events) + chunk_size - 1) // chunk_size

            for chunk_idx in range(0, len(events), chunk_size):
                chunk_events = events[chunk_idx:chunk_idx + chunk_size]
                chunk_created = 0
                chunk_updated = 0
                chunk_skipped = 0

                for event in chunk_events:
                    processed_count += 1
                    emp_no = event.get("employeeNoString")
                    pass_time_str = event.get("time")
                    attendance_status = event.get("attendanceStatus")
                    inferred_status = False

                    if not emp_no or not pass_time_str:
                        chunk_skipped += 1
                        continue

                    if attendance_status is None:
                        minor = event.get("minor")
                        if minor in [75, 38, 181]:
                            attendance_status = "checkIn"
                            inferred_status = True
                        else:
                            chunk_skipped += 1
                            continue

                    employee = self.env["hr.employee"].search(
                        [("hikvision_number", "=", emp_no)], limit=1
                    )
                    if not employee:
                        chunk_skipped += 1
                        continue

                    try:
                        pass_time = datetime.strptime(pass_time_str, "%Y-%m-%dT%H:%M:%S%z")
                        pass_time = pass_time.astimezone(pytz.UTC).replace(tzinfo=None)
                    except ValueError:
                        chunk_skipped += 1
                        continue

                    if pass_time < employee.create_date.replace(tzinfo=None):
                        chunk_skipped += 1
                        continue

                    existing_attendance = self.env["hr.attendance"].search([
                        ("employee_id", "=", employee.id),
                        "|",
                        ("check_in", "=", pass_time),
                        ("check_out", "=", pass_time)
                    ], limit=1)

                    if existing_attendance:
                        chunk_skipped += 1
                        continue

                    if attendance_status == "checkIn":
                        same_day_attendance = self.env["hr.attendance"].search([
                            ("employee_id", "=", employee.id),
                            ("check_in", ">=", pass_time.replace(hour=0, minute=0, second=0, microsecond=0)),
                            ("check_in", "<=", pass_time.replace(hour=23, minute=59, second=59, microsecond=999999)),
                        ], order="check_in desc", limit=1)

                        last_attendance = self.env["hr.attendance"].search(
                            [("employee_id", "=", employee.id)],
                            order="check_in desc",
                            limit=1,
                        )

                        if same_day_attendance and not same_day_attendance.check_out:
                            if inferred_status and pass_time > same_day_attendance.check_in:
                                same_day_attendance.sudo().write({"check_out": pass_time})
                                chunk_updated += 1
                                continue
                            chunk_skipped += 1
                            continue

                        if same_day_attendance and same_day_attendance.check_out:
                            if pass_time > same_day_attendance.check_out:
                                self.env["hr.attendance"].sudo().create({
                                    "employee_id": employee.id,
                                    "check_in": pass_time,
                                })
                                chunk_created += 1
                                continue
                            else:
                                chunk_skipped += 1
                                continue

                        user_tz = self.env.user.tz or "UTC"
                        local_tz = pytz.timezone(user_tz)

                        if last_attendance and not last_attendance.check_out:
                            checkin_date_local = last_attendance.check_in.astimezone(local_tz).date()
                            end_of_day_local = datetime.combine(checkin_date_local, dt_time(23, 59, 59))
                            end_of_day_local = local_tz.localize(end_of_day_local)
                            end_of_day_utc = end_of_day_local.astimezone(pytz.UTC).replace(tzinfo=None)

                            last_attendance.sudo().write({"check_out": end_of_day_utc})
                            chunk_updated += 1

                        if last_attendance and not last_attendance.check_out and pass_time > last_attendance.check_in:
                            safe_checkout = pass_time - timedelta(seconds=1)
                            last_attendance.sudo().write({"check_out": safe_checkout})
                            chunk_updated += 1

                        try:
                            self.env["hr.attendance"].sudo().create({
                                "employee_id": employee.id,
                                "check_in": pass_time,
                            })
                            chunk_created += 1
                        except ValidationError:
                            open_att = self.env["hr.attendance"].search([
                                ("employee_id", "=", employee.id),
                                ("check_out", "=", False)
                            ], order="check_in desc", limit=1)
                            if open_att and pass_time > open_att.check_in:
                                open_att.sudo().write({"check_out": pass_time - timedelta(seconds=1)})
                                chunk_updated += 1
                                self.env["hr.attendance"].sudo().create({
                                    "employee_id": employee.id,
                                    "check_in": pass_time,
                                })
                                chunk_created += 1
                            else:
                                raise

                    elif attendance_status == "checkOut":
                        last_attendance = self.env["hr.attendance"].search([
                            ("employee_id", "=", employee.id),
                        ], order="check_in desc", limit=1)

                        if last_attendance:
                            if not last_attendance.check_out:
                                if pass_time > last_attendance.check_in:
                                    last_attendance.sudo().write({"check_out": pass_time})
                                    chunk_updated += 1
                                else:
                                    chunk_skipped += 1
                            else:
                                chunk_skipped += 1
                        else:
                            self.env["hr.attendance"].sudo().create({
                                "employee_id": employee.id,
                                "check_in": pass_time,
                                "check_out": pass_time + timedelta(seconds=1),
                            })
                            chunk_created += 1

                created_count += chunk_created
                updated_count += chunk_updated
                skipped_count += chunk_skipped

                try:
                    self.env.cr.commit()
                except Exception:
                    self.env.cr.rollback()
                    continue

                job = self.env.context.get('job')
                if job:
                    try:
                        progress = min(100, int((chunk_idx + chunk_size) * 100 / len(events)))
                        if hasattr(job, 'set_progress'):
                            job.set_progress(chunk_idx + chunk_size, total=len(events))
                        elif hasattr(job, 'progress'):
                            job.progress = progress
                    except Exception:
                        pass

                time_module.sleep(0.1)

            return f"All attendance download completed successfully. Processed {processed_count} events, Created {created_count} records, Updated {updated_count} records, Skipped {skipped_count} events"

        except Exception as e:
            try:
                self.env.cr.rollback()
            except:
                pass
            raise e

    def fetch_employees(self):
        """Fetch employees from device and sync with Odoo."""
        for device in self:
            url, auth, headers = self._get_api_config("/ISAPI/AccessControl/UserInfo/Search?format=json")

            payload = {
                "UserInfoSearchCond": {
                    "searchID": "1",
                    "searchResultPosition": 0,
                    "maxResults": 50
                }
            }
            fetched_emp_ids = []
            try:
                response = requests.post(url, auth=auth, json=payload, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    employees = data.get("UserInfoSearch", {}).get("UserInfo", [])
                    for emp in employees:
                        emp_no = emp.get("employeeNo")
                        emp_name = emp.get("name")
                        if not emp_no:
                            continue
                        existing_emp = self.env["hr.employee"].search([("hikvision_number", "=", emp_no)], limit=1)
                        if existing_emp:
                            existing_emp.write({
                                "name": emp_name or existing_emp.name
                            })
                            fetched_emp_ids.append(existing_emp.id)
                        else:
                            new_emp = self.env["hr.employee"].create({
                                "name": emp_name or "Unknown",
                                "hikvision_number": emp_no
                            })
                            fetched_emp_ids.append(new_emp.id)
                    self.env.cr.commit()
                    return {
                        "type": "ir.actions.act_window",
                        "name": _("Fetched Employees"),
                        "res_model": "hr.employee",
                        "view_mode": "list,form",
                        "domain": [("id", "in", fetched_emp_ids)],
                    }
            except requests.exceptions.RequestException:
                pass

    def fetch_logs(self):
        """Fetch and store attendance logs."""
        events = self.fetch_attendance()

        minor_to_attendance_type = {
            38: '1',
            75: '15',
            181: '3',
        }
        status_to_punch_type = {
            'checkIn': '0',
            'checkOut': '1',
            'breakOut': '2',
            'breakIn': '3',
            'overtimeIn': '4',
            'overtimeOut': '5',
            'duplicate': '255',
        }

        for event in events:
            emp_no = event.get("employeeNoString")
            if not emp_no:
                continue

            emp = self.env['hr.employee'].search([('hikvision_number', '=', emp_no)], limit=1)
            if not emp:
                continue

            punch_time_str = event.get("time")
            if not punch_time_str:
                continue
            try:
                normalized = punch_time_str.replace('Z', '+00:00')
                punch_dt = datetime.fromisoformat(normalized)
                punch_dt = punch_dt.astimezone(pytz.UTC).replace(tzinfo=None)

                if punch_dt < emp.create_date.replace(tzinfo=None):
                    continue

            except Exception:
                try:
                    punch_dt = datetime.strptime(punch_time_str[:19], '%Y-%m-%dT%H:%M:%S')
                except Exception:
                    continue

            minor_raw = event.get("minor")
            try:
                minor_val = int(minor_raw) if minor_raw is not None else None
            except (ValueError, TypeError):
                minor_val = None

            attendance_type = minor_to_attendance_type.get(minor_val, '255')
            punch_type = status_to_punch_type.get(event.get("attendanceStatus"), '255')

            existing_log = self.env['hikvision.logs'].search([
                ('employee_id', '=', emp.id),
                ('punching_time', '=', punch_dt),
                ('punch_type', '=', punch_type),
                ('attendance_type', '=', attendance_type),
            ], limit=1)

            if not existing_log:
                self.env['hikvision.logs'].sudo().create({
                    'date': punch_dt.date(),
                    'employee_id': emp.id,
                    'punch_type': punch_type,
                    'attendance_type': attendance_type,
                    'punching_time': punch_dt,
                })

    def set_time(self):
        """Set device time to system time."""
        now = datetime.now()
        offset_minutes = -int((datetime.utcnow() - now).total_seconds() / 60)
        sign = "+" if offset_minutes >= 0 else "-"
        tz_hours = str(abs(offset_minutes) // 60).zfill(2)
        tz_minutes = str(abs(offset_minutes) % 60).zfill(2)

        local_time_str = now.strftime(f"%Y-%m-%dT%H:%M:%S{sign}{tz_hours}:{tz_minutes}")

        xml_payload = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Time xmlns="http://www.hikvision.com/ver10/XMLSchema">
        <timeMode>manual</timeMode>
        <localTime>{local_time_str}</localTime>
    </Time>
    """

        url = f"http://{self.ip_address}/ISAPI/System/time"
        auth = HTTPDigestAuth(self.username, self.password)

        response = requests.put(
            url,
            auth=auth,
            headers={"Content-Type": "application/xml"},
            data=xml_payload
        )

        if response.status_code == 200:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'Successfully Set the Time',
                    'type': 'success',
                    'sticky': False
                }
            }
        else:
            raise UserError(_("Please Check the Connection"))

    def _get_next_hikvision_employee_no(self):
        """Get next available employee number."""
        url, auth, headers = self._get_api_config("/ISAPI/AccessControl/UserInfo/Search?format=json")

        payload = {
            "UserInfoSearchCond": {
                "searchID": "1",
                "maxResults": 1000,
                "searchResultPosition": 0
            }
        }

        used_numbers = set()
        try:
            resp = requests.post(url, auth=auth, json=payload, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                user_list = data.get("UserInfoSearch", {}).get("UserInfo", [])
                for user in user_list:
                    try:
                        num = int(user.get("employeeNo"))
                        used_numbers.add(num)
                    except (ValueError, TypeError):
                        continue
        except Exception:
            pass

        all_odoo_employees = self.env["hr.employee"].with_context(active_test=False).search([
            ("hikvision_number", "!=", False)
        ])

        for emp in all_odoo_employees:
            try:
                num = int(emp.hikvision_number)
                used_numbers.add(num)
            except (ValueError, TypeError):
                continue

        if used_numbers:
            max_no = max(used_numbers)
            next_no = max_no + 1
        else:
            next_no = 1

        return next_no

    def create_hikvision_user(self, employee):
        """Create user on Hikvision device."""
        new_employee_no = self._get_next_hikvision_employee_no()

        employee.hikvision_number = new_employee_no
        self.env.cr.commit()

        url, auth, headers = self._get_api_config("/ISAPI/AccessControl/UserInfo/Record?format=json")

        payload = {
            "UserInfo": {
                "employeeNo": str(new_employee_no),
                "name": employee.name,
                "userType": "normal",
                "valid": {
                    "enable": True,
                    "beginTime": "2020-01-01T00:00:00",
                    "endTime": "2030-01-01T23:59:59"
                },
                "doorRight": "1",
                "RightPlan": [{
                    "doorNo": 1,
                    "planTemplateNo": "1"
                }],
                "faceURL": ""
            }
        }

        response = requests.post(url, auth=auth, json=payload, headers=headers, timeout=10)
        if response.status_code in (200, 201):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _('User created successfully on Hikvision device with ID: %s') % new_employee_no,
                    'type': 'success',
                    'sticky': False
                }
            }
        else:
            employee.hikvision_number = False
            self.env.cr.commit()
            raise UserError(_("Failed to create user: %s") % response.text)

    def update_hikvision_user(self, employee):
        """Update user on Hikvision device."""
        if not employee.hikvision_number:
            raise UserError(_("This employee does not have a Hikvision number."))

        url, auth, headers = self._get_api_config("/ISAPI/AccessControl/UserInfo/Modify?format=json")

        payload = {
            "UserInfo": {
                "employeeNo": employee.hikvision_number,
                "name": employee.name,
                "userType": "normal",
                "valid": {
                    "enable": True,
                    "beginTime": "2020-01-01T00:00:00",
                    "endTime": "2030-01-01T23:59:59"
                },
                "doorRight": "1",
                "RightPlan": [{
                    "doorNo": 1,
                    "planTemplateNo": "1"
                }],
                "faceURL": ""
            }
        }

        response = requests.put(url, auth=auth, json=payload, headers=headers, timeout=10)
        if response.status_code in (200, 201):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _('User updated successfully on Hikvision device.'),
                    'type': 'success',
                    'sticky': False
                }
            }
        else:
            raise UserError(_("Failed to update user: %s") % response.text)

    def archive_hikvision_user(self, employee):
        """Delete user from Hikvision device when archived."""
        if not employee.hikvision_number:
            raise UserError(_("This employee does not have a Hikvision number."))

        url, auth, headers = self._get_api_config("/ISAPI/AccessControl/UserInfo/Delete?format=json")

        payload = {
            "UserInfoDelCond": {
                "EmployeeNoList": [
                    {
                        "employeeNo": employee.hikvision_number
                    }
                ]
            }
        }

        try:
            response = requests.put(url, auth=auth, json=payload, headers=headers, timeout=10)
        except requests.RequestException as e:
            raise UserError(_("Connection error: %s") % e)

        if response.status_code in (200, 201):
            employee.active = False
            self.env.cr.commit()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _(
                        'User deleted from device successfully. ID %s preserved in Odoo.') % employee.hikvision_number,
                    'type': 'success',
                    'sticky': False
                }
            }
        else:
            raise UserError(_("Failed to delete user from device: %s") % response.text)

    def delete_hikvision_user(self, employee):
        """Delete user from Hikvision device."""
        return self.archive_hikvision_user(employee)

    @api.model
    def cron_download_attendance_all_devices(self):
        """Cron job to download attendance from all devices daily."""
        devices = self.search([])

        success_count = 0
        error_count = 0

        for device in devices:
            try:
                device.fetch_and_create_attendance()
                success_count += 1
                time_module.sleep(2)
            except Exception:
                error_count += 1
                continue

        return True
