#!/usr/bin/env python3
#
# Usage:
#   simple-scheduler.py <cron expression> <command>
#

import sys
import subprocess
import time
from datetime import datetime
from cron_converter import Cron

cron = Cron(sys.argv[1])
schedule = cron.schedule(datetime.now())

exec_cmd = sys.argv[2:]

while True:
  # sleep until the next scheduled run time
  when = schedule.next()
  print(f'Sleeping until {when.isoformat()}')
  sleep_time = (when - datetime.now()).total_seconds()
  time.sleep(sleep_time)

  # execute the task
  try:
    subprocess.run(exec_cmd)
  except:
    print(f' - Failed to run job command: {sys.exc_info()[1]}')

  print()