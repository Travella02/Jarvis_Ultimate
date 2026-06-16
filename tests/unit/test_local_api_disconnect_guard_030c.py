from __future__ import annotations

import unittest

from jarvis.api.local_server import _is_client_disconnect_error


class TestLocalApiDisconnectGuard030c(unittest.TestCase):
    def test_expected_client_disconnect_errors_are_suppressed(self):
        self.assertTrue(_is_client_disconnect_error(BrokenPipeError()))
        self.assertTrue(_is_client_disconnect_error(ConnectionResetError()))
        self.assertTrue(_is_client_disconnect_error(ConnectionAbortedError()))

    def test_windows_abort_error_code_is_treated_as_client_disconnect(self):
        error = OSError("client disconnected")
        error.winerror = 10053
        self.assertTrue(_is_client_disconnect_error(error))

    def test_unrelated_os_error_is_not_suppressed(self):
        self.assertFalse(_is_client_disconnect_error(OSError(5, "access denied")))


if __name__ == "__main__":
    unittest.main()
