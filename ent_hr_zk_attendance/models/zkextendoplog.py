# -*- coding: utf-8 -*-
################################################################################
#
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
def zkextendoplog(self, index=0):
    """Send the command that requests extended operation log data."""
    try:
        test = self.extlogtrynumber
    except:
        self.extlogtrynumber = 1

    data_hex = self.data_recv.hex()
    data_seq = [data_hex[4:6], data_hex[6:8]]

    if index == 0:
        self.data_seq1 = hex(int(data_seq[0], 16) + int('104', 16)).lstrip("0x")
        self.data_seq2 = hex(int(data_seq[1], 16) + int('19', 16)).lstrip("0x")
        desc = ": +104, +19"
        header = "0b00"
    elif index == 1:
        self.data_seq1 = hex(abs(int(data_seq[0], 16) - int('2c', 16))).lstrip(
            "0x")
        self.data_seq2 = hex(abs(int(data_seq[1], 16) - int('2', 16))).lstrip(
            "0x")
        desc = ": -2c, -2"
        header = "d107"
    elif index >= 2:
        self.data_seq1 = hex(abs(int(data_seq[0], 16) - int('2c', 16))).lstrip(
            "0x")
        self.data_seq2 = hex(abs(int(data_seq[1], 16) - int('2', 16))).lstrip(
            "0x")
        desc = ": -2c, -2"
        header = "ffff"

    if len(self.data_seq1) >= 3:
        self.data_seq2 = hex(
            int(self.data_seq2, 16) + int(self.data_seq1[:1], 16)).lstrip("0x")
        self.data_seq1 = self.data_seq1[-2:]

    if len(self.data_seq2) >= 3:
        self.data_seq1 = hex(
            int(self.data_seq1, 16) + int(self.data_seq2[:1], 16)).lstrip("0x")
        self.data_seq2 = self.data_seq2[-2:]

    if len(self.data_seq1) <= 1:
        self.data_seq1 = "0" + self.data_seq1

    if len(self.data_seq2) <= 1:
        self.data_seq2 = "0" + self.data_seq2

    counter = hex(self.counter).lstrip("0x")
    if len(counter):
        counter = "0" + counter

    data = (header + self.data_seq1 + self.data_seq2 + self.id_com + counter +
            "00457874656e644f504c6f6700")
    self.zkclient.sendto(bytes.fromhex(data), self.address)
    try:
        self.data_recv, addr = self.zkclient.recvfrom(1024)
    except:
        if self.extlogtrynumber == 1:
            self.extlogtrynumber = 2
            zkextendoplog(self)
    self.id_com = self.data_recv.hex()[8:12]
    self.counter = self.counter + 1
    return self.data_recv[8:]
