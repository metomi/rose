# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-6 Met Office.
#
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
"""A crude URL validator"""
from multiprocessing import Pool
import os
import re
import requests
import sys
import warnings

# Ignore warnings raised as a result of negating verification in ssl requests.
from requests.packages.urllib3.exceptions import InsecureRequestWarning
warnings.filterwarnings('ignore', category=InsecureRequestWarning)


# Regexes.
URL_PATTERN = re.compile(r'<(?:a|img|link|script)[^>]+(?:src|href)='
                         r'(?:[\s\n]+)?"([^"]+)"(?:[^>]+)?>')
FRAG_PATTERN = re.compile(r'(?:id)=(?:[\n\s]+)?"([^"]+)"')

# External URL validation parameters.
POOL_THROTTLE = 5
TIMEOUT = 5

# Error types.
PAGE_NOT_FOUND = 'Page not found'
FRAGMENT_NOT_FOUND = 'Fragment not found'
URL_REDIRECT = 'Encountered a permanent redirect'
URL_TIMEOUT_STRING = 'Server timeout.'
INVALID_URL = 'Invalid URL'
CONNECTION_ERROR = 'Connection error.'
HTTP_ERROR = 'Non 2xx return code detected "{0}".'


def get_files_by_extension(root_dir, extension):
    """Rough equivalent to `find <root_dir> -name \*.<extension>`."""
    for root, _, files in os.walk(root_dir):
        for file_ in files:
            if os.path.splitext(file_)[1] != '.' + extension:
                continue
            yield os.path.join(root, file_)

def validate_fragments(fragments):
    """Ensure URL fragments for internal links match DOM elements (id=...)."""
    errors = []
    ids = {}
    for fragment, file_, src in fragments:
        if file_ not in ids:
            if not os.path.exists(file_):
                errors.append((fragment, file_, PAGE_NOT_FOUND))
                continue
            with open(file_, 'r') as html_file:
                matches = FRAG_PATTERN.findall(html_file.read())
                ids[file_] = matches
        if fragment not in ids[file_]:
            errors.append((file_ + '#' + fragment, src, FRAGMENT_NOT_FOUND))
    return errors

def validate_internal(urls):
    """Ensure internal URLs match files, return URL fragments for further
    validation."""
    errors = []
    fragments = []
    for url, file_ in urls:
        if '#' in url:
            path, fragment = url.rsplit('#', 1)
        else:
            path = url
            fragment = None
        path = os.path.join(os.path.dirname(file_), path)
        if not os.path.exists(path):
            errors.append((url, file_, PAGE_NOT_FOUND))
            continue
        if fragment:
            fragments.append((fragment, path, file_))
    return errors, fragments

def validate_external(urls):
    """Ensure external URLs point to valid sites.

    Uses a multiprocessing pool for performing http requests."""
    errors = []
    pool = Pool(POOL_THROTTLE)
    rets = pool.map(validate_url, urls.keys())
    for error, (url, file_) in zip(rets, urls.iteritems()):
        if error:
            errors.append((url, file_, error,))
    return errors

def validate_url(url, full=False, verify=True):
    """Test that a URL points to a valid page.

    Ignores status codes 2xx, 301, 302, 303, 308, reports anything else."""
    # Some sites don't like the python user agent.
    headers = {'User-Agent': 'Mozilla/5.0'}
    # Request method.
    if full:
        method = requests.get
    else:
        method = requests.head
    try:
        response = method(url, timeout=TIMEOUT, allow_redirects=True,
                          headers=headers, verify=verify)
    except requests.exceptions.Timeout:
        return URL_TIMEOUT_STRING
    except requests.exceptions.MissingSchema:
        return INVALID_URL
    except requests.exceptions.ConnectionError:
        if verify:
            # Try again without ssl verification (ok with safe urls).
            return validate_url(url, full, verify=False)
        return CONNECTION_ERROR
    except requests.exceptions.HTTPError:
        return PAGE_NOT_FOUND
    else:
        code = int(response.status_code)
        if code in [301, 302, 303, 308]:
            #errors.append((url, file_, URL_REDIRECT))
            pass
        if code == 405 and not full:
            # If we get a "method not allowed" try using a get request (slow).
            return validate_url(url, full=True)
        elif code < 200 or code >= 300:
            return HTTP_ERROR.format(code)
    return None

def report_invalid_urls(int_errors, ext_errors, frg_errors, malformed):
    """Print out list of errors."""
    errors_by_file = {}
    for url, file_, error in int_errors + ext_errors + frg_errors + malformed:
        if file_ not in errors_by_file:
            errors_by_file[file_] = []
        errors_by_file[file_].append((url, error,))

    if errors_by_file:
        print >> sys.stderr, 'Errors found in the following files:'
    for file_, errors in errors_by_file.iteritems():
        print >> sys.stderr
        print >> sys.stderr, '\t', file_
        for url, error in errors:
            print >> sys.stderr, '\t\t"{url}"  -  "{error}"'.format(
                url=url, error=error)

def main(root):
    """Extract and check all URLs on the site located at root."""
    external = {}
    internal = []
    fragments = []
    malformed = []
    for file_ in get_files_by_extension(root, 'html'):
        with open(file_, 'r') as html_file:
            matches = URL_PATTERN.findall(html_file.read())
            for url in matches:
                if url.startswith('mailto:'):
                    # We aren't validating email addresses.
                    continue
                if url.startswith('javascript:'):
                    # We arent validating javascript functions.
                    continue
                if url.startswith('#') and len(url) > 1:
                    # URL fragment (on current page).
                    fragments.append((url[1:], file_, file_))
                elif url.startswith('www.'):
                    malformed.append((url, file_, INVALID_URL))
                elif url.startswith('http'):
                    if url not in external:
                        external[url] = file_
                else:
                    internal.append((url, file_,))

    int_errors, new_frags = validate_internal(internal)
    ext_errors = validate_external(external)
    frg_errors = validate_fragments(new_frags + fragments)

    report_invalid_urls(int_errors, ext_errors, frg_errors, malformed)

    if int_errors or ext_errors or frg_errors or malformed:
        sys.exit(1)
    sys.exit(0)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('Usage: Please supply root directory to validate the '
                 'contents of.')
    main(sys.argv[1])
