# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-3 Met Office.
#
# This file is part of Rose, a framework for scientific suites.
#
# Rose is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Rose is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Rose. If not, see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------
"""Compress archive sources in tar."""

import os
import tarfile
from tempfile import mkstemp


class RoseArchTarGzip(object):

    """Compress archive sources in tar."""

    SCHEMES = ["pax", "pax.gz", "tar", "tar.gz", "tgz"]
    SCHEME_EXTS = {"pax.gz": ":gz", "tar.gz": ":gz", "tgz": ":gz"}
    SCHEME_FORMATS = {"pax": tarfile.PAX_FORMAT, "pax.gz": tarfile.PAX_FORMAT}

    def __init__(self, app_runner, *args, **kwargs):
        self.app_runner = app_runner

    def compress_sources(self, target, work_dir):
        """Create a tar archive of all files in target.

        Use work_dir to dump results.

        """
        sources = target.sources.values()
        scheme = target.compress_scheme
        if (len(sources) == 1 and
            sources[0].path.endswith("." + target.compress_scheme)):
            target.work_source_path = sources[0].path
            return # Assume that it has been done
        fd, tmp_name = mkstemp(suffix="." + target.compress_scheme, dir=work_dir)
        os.close(fd)
        target.work_source_path = tmp_name
        scheme_ext = self.SCHEME_EXTS.get(target.compress_scheme, "")
        scheme_format = self.SCHEME_FORMATS.get(target.compress_scheme,
                                                tarfile.DEFAULT_FORMAT)
        f_bsize = os.statvfs(work_dir).f_bsize
        t = tarfile.open(tmp_name, "w" + scheme_ext, bufsize=f_bsize,
                         format=scheme_format)
        for source in sources:
            f = open(source.path)
            tarinfo = t.gettarinfo(arcname=source.name, fileobj=f)
            t.addfile(tarinfo, f)
        t.close()
