# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

"""Transcribes one uploaded meeting recording in a detached process (started by ``stt_client.start_job``).

A whole recording can take far longer to transcribe than Odoo lets an HTTP request or a cron
job run (``limit_time_real``), so it runs here, outside any Odoo worker: nothing kills it when
a worker times out or is recycled. Like ``stt_worker``, it must not import Odoo.

Usage: ``python stt_job.py <job_dir>``. The job directory holds:
  request.json : {"engine": "grok"|"whisper", "audio": file name, "language", "model",
                  "keywords", "main_language", "api_key" (grok only)}
  <audio>      : the recording
It writes ``heartbeat`` while running, then ``result.json``:
  {"text": str, "duration": float|None} or {"error": str}
"""
import contextlib
import json
import logging
import os
import resource
import sys
import threading
import time

HEARTBEAT_SECONDS = 20

_logger = logging.getLogger("stt_job")


def write_json(job_dir, name, data):
    # written aside then renamed, so Odoo never reads a half-written result
    tmp = os.path.join(job_dir, name + ".tmp")
    with open(tmp, "w") as f:
        json.dump(data, f)
    os.replace(tmp, os.path.join(job_dir, name))


def heartbeat(job_dir, stop):
    path = os.path.join(job_dir, "heartbeat")
    while not stop.is_set():
        try:
            with open(path, "w") as f:
                f.write(str(time.time()))
        except OSError:
            return  # the job was cancelled: its directory is gone
        stop.wait(HEARTBEAT_SECONDS)


def run(job_dir, request):
    with open(os.path.join(job_dir, request["audio"]), "rb") as f:
        audio = f.read()
    if request["engine"] == "grok":
        import grok_stt
        result = grok_stt.transcribe(
            audio, request["api_key"], filename=request["audio"], language=request.get("language"),
            keywords=request.get("keywords"), diarize=True, timeout=(10, 3600),
        )
        return {"text": grok_stt.speaker_transcript(result), "duration": result.get("duration")}
    import stt_worker
    stt_worker.patch_faster_whisper_av()
    result = stt_worker.transcribe_whisper(
        audio, request.get("language"), request.get("model") or "small", request.get("keywords") or [],
        beam_size=5, main_language=request.get("main_language"),
    )
    return {"text": result["text"], "duration": result.get("duration")}


def main():
    # its stderr is the job log (job.log)
    logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="[%(name)s] %(message)s")
    job_dir = sys.argv[1]
    # Odoo's address-space cap is inherited by child processes; the models need far more.
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    if soft != hard:
        resource.setrlimit(resource.RLIMIT_AS, (hard, hard))
    stop = threading.Event()
    threading.Thread(target=heartbeat, args=(job_dir, stop), daemon=True).start()
    try:
        with open(os.path.join(job_dir, "request.json")) as f:
            request = json.load(f)
        reply = run(job_dir, request)
    except ImportError as exc:
        reply = {"error": "not_installed: %s" % exc}
    except Exception as exc:  # reported to Odoo, which marks the recording as failed
        _logger.error("failed: %r", exc)
        reply = {"error": str(exc) or repr(exc)}
    stop.set()
    with contextlib.suppress(OSError):  # cancelled meanwhile
        write_json(job_dir, "result.json", reply)


if __name__ == "__main__":
    main()
