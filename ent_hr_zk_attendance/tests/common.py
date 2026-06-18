# -*- coding: utf-8 -*-

import datetime
from struct import pack
from types import SimpleNamespace
from unittest.mock import Mock

from odoo.tests.common import TransactionCase

from odoo.addons.ent_hr_zk_attendance.models import zkconst


def reply_packet(command=zkconst.CMD_ACK_OK, session_id=5, reply_id=7, payload=b"DATA"):
    return pack("HHHH", command, 0, session_id, reply_id) + payload


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.sent = []

    def sendto(self, data, address):
        self.sent.append((data, address))

    def recvfrom(self, _size):
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response, ("127.0.0.1", 4370)


def fake_device_state(responses, data_recv=None):
    return SimpleNamespace(
        session_id=1,
        address=("127.0.0.1", 4370),
        data_recv=data_recv or reply_packet(),
        zkclient=FakeClient(responses),
        createHeader=Mock(return_value=b"HEADER"),
        checkValid=Mock(return_value=True),
        userdata=[],
        attendancedata=[],
        id_com="0102",
        counter=1,
    )


class EntZkTransactionCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env.ref("base.partner_admin")
        cls.employee = cls.env.ref("hr.employee_admin", raise_if_not_found=False) or cls.env["hr.employee"].search([], limit=1)
        cls.machine = cls.env["zk.machine"].create({
            "name": "192.168.0.10",
            "port_no": 4370,
            "address_id": cls.partner.id,
        })


def sample_datetime():
    return datetime.datetime(2026, 5, 14, 9, 30, 45)
