import unittest
import time
from threading import Thread

from robothub_sdk import App


class TestAppLifecycle(unittest.TestCase):
    class AppWithoutDevices(App):
        def __init__(self):
            super().__init__(run_without_devices=True)

    def setUp(self) -> None:
        self.app = TestAppLifecycle.AppWithoutDevices()
        self.thread = Thread(target=self.app.run, daemon=True)
        self.thread.start()
        time.sleep(1)

    def tearDown(self) -> None:
        self.app.stop()
        self.thread.join()

    def test_restart(self):
        self.assertEqual(self.app.running, True)
        self.app.restart()
        self.assertEqual(self.app.running, True)
        self.app.restart()
        self.assertEqual(self.app.running, True)


if __name__ == "__main__":
    unittest.main()
