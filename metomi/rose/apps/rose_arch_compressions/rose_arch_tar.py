# Copyright (C) British Crown (Met Office) & Contributors.
# This file is part of Rose, a framework for meteorological suites.
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
# -----------------------------------------------------------------------------
"""Compress archive sources in tar."""

import os
import tarfile
from tempfile import mkstemp

from metomi.rose.apps.rose_arch_compressions import (
    RoseArchCompressThreadsError,
)

from metomi.rose.apps.rose_arch_compressions import rose_arch_gzip
from metomi.rose.apps.rose_arch_compressions import rose_arch_xz
from metomi.rose.apps.rose_arch_compressions import rose_arch_zstd


class RoseArchTarGzip:

    """Compress archive sources in tar."""

    # Compression scheme: compressor class to apply to the tar file.
    COMPRESSORS = {
        "pax.gz": rose_arch_gzip.RoseArchGzip,
        "tar.gz": rose_arch_gzip.RoseArchGzip,
        "tgz": rose_arch_gzip.RoseArchGzip,
        "pax.xz": rose_arch_xz.RoseArchXz,
        "tar.xz": rose_arch_xz.RoseArchXz,
        "txz": rose_arch_xz.RoseArchXz,
        "pax.zst": rose_arch_zstd.RoseArchZstd,
        "tar.zst": rose_arch_zstd.RoseArchZstd,
        "tzst": rose_arch_zstd.RoseArchZstd,
    }
    SCHEMES = ["pax", "tar"] + list(COMPRESSORS)
    SCHEME_FORMATS = {
        scheme: tarfile.PAX_FORMAT
        for scheme in SCHEMES
        if scheme.startswith("pax")
    }

    def __init__(self, app_runner, *args, **kwargs):
        self.app_runner = app_runner

    @classmethod
    def supports_threads(cls, scheme):
        """Return True if "scheme" can be compressed with many threads."""
        compressor = cls.COMPRESSORS.get(scheme)
        return compressor is not None and compressor.MULTI_THREADED

    def compress_sources(self, target, work_dir, threads=1):
        """Create a tar archive of all files in target.

        Use work_dir to dump results.

        """
        compressor = self.COMPRESSORS.get(target.compress_scheme)
        if compressor is not None:
            compressor.check_threads(threads)
        elif threads != 1:
            raise RoseArchCompressThreadsError(target.compress_scheme)

        sources = list(target.sources.values())
        if len(sources) == 1 and sources[0].path.endswith(
            "." + target.compress_scheme
        ):
            target.work_source_path = sources[0].path
            return  # Assume that it has been done
        fdsec, tar_name = mkstemp(suffix=".tar", dir=work_dir)
        os.close(fdsec)
        target.work_source_path = tar_name
        scheme_format = self.SCHEME_FORMATS.get(
            target.compress_scheme, tarfile.DEFAULT_FORMAT
        )
        f_bsize = os.statvfs(work_dir).f_bsize
        # @TODO This is not very Python3: context managers and tarhandle.add
        tarhandle = tarfile.open(
            tar_name, "w", bufsize=f_bsize, format=scheme_format
        )
        for source in sources:
            handle = open(source.path, 'rb')
            tarinfo = tarhandle.gettarinfo(arcname=source.name, fileobj=handle)
            tarhandle.addfile(tarinfo, handle)
        tarhandle.close()

        if compressor is not None:
            fdsec, work_path = mkstemp(
                suffix="." + target.compress_scheme, dir=work_dir
            )
            os.close(fdsec)
            target.work_source_path = work_path
            compressor.compress(self.app_runner, tar_name, work_path, threads)
            self.app_runner.fs_util.delete(tar_name)
