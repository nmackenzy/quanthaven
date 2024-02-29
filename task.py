# IMPORT MODULES
import multiprocessing
# IMPORT USER-DEFINED PACKAGES
from historicalbot.hist_main import HistoricalBot
from livebot.live_main import LiveBot


class Task:
    def __init__(self, data_queue, stdout_queue):
        self._running = multiprocessing.Value('b', False)
        self._thread = None
        self.data_queue = data_queue
        self.stdout_queue = stdout_queue
        self.bot = None

    def _run(self):
        while self._running.value:
            print("Task is running")
            with open('bot_configuration.txt', 'r') as f:
                content = f.read()
                content_list = content.split('$')
            if content_list[3] == 'Historical':
                self.bot = HistoricalBot(self.data_queue, self.stdout_queue)
                self.bot.start()
            elif content_list[3] == 'Live':
                self.bot = LiveBot(self.data_queue, self.stdout_queue)
                self.bot.start()
            else:
                self.stop()

    def start(self):
        if self._running.value:  # Check if the task is already running
            print("Task is already running")
        else:
            self._running.value = True
            self._thread = multiprocessing.Process(target=self._run)
            self._thread.start()

    def stop(self):
        if self.bot:
            self.bot.stop()
        self._running.value = False
        print("Task stopped")
        if self._thread is not None:
            self._thread.terminate()
            self._thread = None
