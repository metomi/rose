import errno
import os
import unittest

from rose.popen import RosePopenError, RosePopener


class _TestOSErrorFilename(unittest.TestCase):
    """Ensure an OSError has a filename."""

    def test_oserror_has_filename(self):
        """Does what it says."""
        rose_popen = RosePopener()
        name = "bad-command"
        try:
            rose_popen.run(name)
        except RosePopenError as exc:
            ose = FileNotFoundError(errno.ENOENT,
                                    os.strerror(errno.ENOENT),
                                    name)
            try:
                self.assertEqual(str(ose), exc.stderr)
            except AssertionError:
                # This is horrible, but refers to a bug in some versions of
                # Python 2.6 - https://bugs.python.org/issue32490
                err_msg = ("[Errno 2] No such file or directory:"
                           " 'bad-command': 'bad-command'")
                self.assertEqual(err_msg, exc.stderr)
        else:
            self.fail("should return FileNotFoundError")


if __name__ == '__main__':
    unittest.main()
