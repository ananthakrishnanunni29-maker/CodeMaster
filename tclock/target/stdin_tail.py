import sys
import os
import time
import select
from datetime import datetime, timedelta
from bignum import time_string

IS_WINDOWS = sys.platform == "win32"


def stdin_tail(cfg) -> int:
    ap = cfg.ap
    blink = False
    prev_now = None
    prev = ""
    max_poll = 0.1

    try:
        while True:
            do_draw = cfg.breath
            now = datetime.now()
            
            if cfg.count_down:
                left = cfg.end - now
                if left.total_seconds() < 0:
                    ap.write_string(f"\n\n\aTime's up reached at {cfg.format_time(now)}\r\n")
                    return 0
                num_str = cfg.duration_string(left, cfg.seconds)
            else:
                num_str = cfg.format_time(now)

            if num_str != prev:
                do_draw = True
            prev = num_str

            truncated_now = now.replace(microsecond=0)
            if truncated_now != prev_now and cfg.blink_enabled:
                blink = not blink
                do_draw = True
            prev_now = truncated_now

            # Read stdin non-blocking
            buf = ""
            if IS_WINDOWS:
                # Windows stdin check
                time.sleep(max_poll)
            else:
                rlist, _, _ = select.select([sys.stdin], [], [], max_poll)
                if rlist:
                    buf = sys.stdin.read(4096)

            n = len(buf)

            if do_draw or n > 0:
                cfg.frame += 1
                ap.start_sync_mode()
                if n > 0:
                    ap.Out.write(buf)
                    ap.save_cursor_pos()
                cfg.draw_at(-1, -1, time_string(num_str, blink))
                ap.restore_cursor_pos()
                ap.end_sync_mode()

    except KeyboardInterrupt:
        return 0
