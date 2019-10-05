from supervisor import Supervisor
from WindowsSleepInhibitor import WindowsSleepInhibitor

import sys

osSleep = None
# in Windows, prevent the OS from sleeping while we run
if sys.platform == 'win32':
    osSleep = WindowsSleepInhibitor()
    osSleep.inhibit()

supervisor = Supervisor(dev=True, archive=False)
supervisor.run()

# Remove sleep inhibition
if osSleep:
    osSleep.uninhibit()