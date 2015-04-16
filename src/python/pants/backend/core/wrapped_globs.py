# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

import os

from six import string_types
from twitter.common.dirutil.fileset import Fileset

from pants.base.build_environment import get_buildroot


class FilesetWithSpec(object):
  """A set of files with that keeps track of how we got it.

  The spec is what globs or file list it came from.
  """
  def __init__(self, result, spec):
    self._result = result
    self.spec = spec

  def __iter__(self):
    return self._result.__iter__()


class FilesetRelPathWrapper(object):
  def __init__(self, parse_context):
    self.rel_path = parse_context.rel_path

  def __call__(self, *args, **kwargs):
    root = os.path.join(get_buildroot(), self.rel_path)

    excludes = kwargs.pop('exclude', [])
    if isinstance(excludes, string_types):
        raise ValueError("Expected exclude parameter to be a list of globs, lists, or strings")

    for i, exclude in enumerate(excludes):
      if isinstance(exclude, string_types):
        # You can't subtract raw strings from globs
        excludes[i] = [exclude]

    for glob in args:
      if(self._is_glob_dir_outside_root(glob, root)):
        raise ValueError('Invalid glob {}, points outside BUILD file root dir {}'.format(glob, root))

    result = self.wrapped_fn(root=root, *args, **kwargs)

    for exclude in excludes:
      result -= exclude

    buildroot = get_buildroot()
    rel_root = os.path.relpath(root, buildroot)
    filespec = self.to_json(args, root=rel_root, excludes=excludes)
    return FilesetWithSpec(result, filespec)

  def _is_glob_dir_outside_root(self, glob, root):
    # The assumption is that a correct glob starts with the root,
    # even after normalizing.
    glob_path = os.path.normpath(os.path.join(root, glob))

    # Check if the glob path has the correct root.
    return os.path.commonprefix([root, glob_path]) != root

  def to_json(self, args, root='', excludes=None):
    """Return a dict representation of this glob list, relative to the buildroot.

    The format of the dict is {'globs': [ 'list', 'of' , 'strings' ]
                    (optional) 'exclude' : [{'globs' : ... }, ...] }

    The globs are in zglobs format.
    """
    result = {'globs' : [os.path.join(root, arg) for arg in args]}
    if excludes:
      result['exclude'] = []
      for exclude in excludes:
        if hasattr(exclude, 'spec'):
          result['exclude'].append(exclude.spec)
        else:
          result['exclude'].append({'globs' : [os.path.join(root, x) for x in exclude]})
    return result

class Globs(FilesetRelPathWrapper):
  """Returns Fileset containing matching files in same directory as this BUILD file.
  E.g., ``sources = globs('*java'),`` to get .java files in this directory.

  :param exclude: a list of {,r,z}globs objects, strings, or lists of
  strings to exclude.  E.g. ``globs('*',exclude=[globs('*.java'),
  'foo.py'])`` gives all files in this directory except ``.java``
  files and ``foo.py``.

  Deprecated:
  You might see that old code uses "math" on the return value of
  ``globs()``.  E.g., ``globs('*') - globs('*.java')`` gives all files
  in this directory *except* ``.java`` files.  Please use exclude
  instead, since pants is moving to make BUILD files easier to parse,
  and the new grammar will not support arithmetic.

  :returns FilesetWithSpec containing matching files in same directory as this BUILD file.
  :rtype FilesetWithSpec

  """
  wrapped_fn = Fileset.globs


class RGlobs(FilesetRelPathWrapper):
  """Recursive ``globs``, returns Fileset matching files in this directory and its descendents.

  E.g., ``bundle(fileset=rglobs('config/*')),`` to bundle up all files in
  the config, config/foo, config/foo/bar directories.

  :param exclude: a list of {,r,z}globs objects, strings, or lists of
  strings to exclude.  E.g. ``rglobs('config/*',exclude=[globs('config/*.java'),
  'config/foo.py'])`` gives all files under config except ``.java`` files and ``config/foo.py``.

  Deprecated:
  You might see that old code uses "math" on the return value of ``rglobs()``. E.g.,
  ``rglobs('config/*') - rglobs('config/foo/*')`` gives all files under `config` *except*
  those in ``config/foo``.  Please use exclude instead, since pants is moving to
  make BUILD files easier to parse, and the new grammar will not support arithmetic.
  :returns FilesetWithSpec matching files in this directory and its descendents.
  :rtype FilesetWithSpec
  """
  @staticmethod
  def rglobs_following_symlinked_dirs_by_default(*globspecs, **kw):
    if 'follow_links' not in kw:
      kw['follow_links'] = True
    return Fileset.rglobs(*globspecs, **kw)

  wrapped_fn = rglobs_following_symlinked_dirs_by_default

  def to_json(self, args, root='', excludes=None):
    return super(RGlobs, self).to_json([os.path.join('**', arg) for arg in args], root=root, excludes=excludes)

class ZGlobs(FilesetRelPathWrapper):
  """Returns a FilesetWithSpec that matches zsh-style globs, including ``**/`` for recursive globbing.

  Uses ``BUILD`` file's directory as the "working directory".
  """
  @staticmethod
  def zglobs_following_symlinked_dirs_by_default(*globspecs, **kw):
    if 'follow_links' not in kw:
      kw['follow_links'] = True
    return Fileset.zglobs(*globspecs, **kw)

  wrapped_fn = zglobs_following_symlinked_dirs_by_default
