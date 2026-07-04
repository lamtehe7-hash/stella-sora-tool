import sys, time
sys.path.insert(0, r'e:\Claude\Stella Sora Tool')
from module.config import Config
from module.device.device import Device
from tasks.ascension import Ascension

config = Config.load()
device = Device(config)
device.connect()
task = Ascension(config, device)
task._run_loop()
print('RESUME DONE')
