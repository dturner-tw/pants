# coding=utf-8
# Copyright 2016 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

import os
from collections import namedtuple
from contextlib import contextmanager

from pants_test.pants_run_integration_test import PantsRunIntegrationTest


class JarDependencyManagementIntegrationTest(PantsRunIntegrationTest):

  JarSet = namedtuple('JarSet', ['jersey', 'jsr311'])

  project = 'testprojects/src/java/org/pantsbuild/testproject/depman'
  manager_target = ':'.join([project, 'manager'])
  manager2_target = ':'.join([project, 'manager2'])
  set_default = JarSet('jersey-0.5-ea', 'jsr311-api-0.5')
  set_managed = JarSet('jersey-0.4-ea', 'jsr311-api-0.7')
  set_managed2 = JarSet('jersey-0.2.1-ea', 'jsr311-api-0.2')

  @contextmanager
  def _testing_build_file(self):
    test_name = os.path.join(self.project, 'TEST_BUILD')
    real_name = os.path.join(self.project, 'BUILD')
    try:
      os.rename(test_name, real_name)
      yield
    finally:
      os.rename(real_name, test_name)

  def _run_project(self, spec_name, default_target=None, conflict_strategy=None):
    with self._testing_build_file():
      return self.run_pants([
        'run',
        '{}:{}'.format(self.project, spec_name),
        '--jar-dependency-management-default-target={}'.format(default_target or ''),
        '--jar-dependency-management-conflict-strategy={}'.format(conflict_strategy or 'FAIL'),
      ])

  def _classpath_result(self, *args, **kwargs):
    run = self._run_project(*args, **kwargs)
    self.assert_success(run)
    return run.stdout_data

  def _assert_classpath_contents(self, expected_sets, spec_name, **kwargs):
    classpath = self._classpath_result(spec_name, **kwargs)
    for jar_set, value in expected_sets.items():
      for jar in jar_set:
        self.assertEquals(value, jar in classpath)

  def test_unmanaged_no_default(self):
    self._assert_classpath_contents({
      self.set_default: True,
      self.set_managed: False,
      self.set_managed2: False,
    }, 'unmanaged')

  def test_unmanaged_default2(self):
    self._assert_classpath_contents({
      self.set_default: False,
      self.set_managed: False,
      self.set_managed2: True,
    }, 'unmanaged', default_target=self.manager2_target, conflict_strategy='USE_MANAGED')

  def test_managed(self):
    self._assert_classpath_contents({
      ('commons-io',): False,
      self.set_default: False,
      self.set_managed: True,
      self.set_managed2: False,
    }, 'managed', conflict_strategy='USE_MANAGED')

  def test_managed_ignore_default(self):
    self._assert_classpath_contents({
      self.set_default: False,
      self.set_managed: True,
      self.set_managed2: False,
    }, 'managed', default_target=self.manager2_target, conflict_strategy='USE_MANAGED')

  def test_managed_auto(self):
    self._assert_classpath_contents({
      self.set_default: False,
      self.set_managed: True,
      self.set_managed2: False,
    }, 'managed-auto')

  def test_managed_use_direct(self):
    self._assert_classpath_contents({
      self.JarSet(self.set_default.jersey, self.set_managed.jsr311): True,
      self.set_managed2: False,
    }, 'managed', conflict_strategy='USE_DIRECT')

  def test_managed_fail(self):
    run = self._run_project('managed', conflict_strategy='FAIL')
    self.assert_failure(run)
    # Check for snippet of expected error message.
    self.assertIn('An artifact directly specified', run.stdout_data)

  def test_unmanaged_fail(self):
    run = self._run_project('unmanaged', default_target=self.manager_target,
                            conflict_strategy='FAIL')
    self.assert_failure(run)
    # Check for snippet of expected error message.
    self.assertIn('An artifact directly specified', run.stdout_data)

  def test_managed_forceful(self):
    self._assert_classpath_contents({
      self.JarSet(self.set_default.jersey, self.set_managed.jsr311): True,
      self.set_managed2: False,
    }, 'forceful', conflict_strategy='USE_DIRECT_IF_FORCED')

  def test_managed_redundant(self):
    self._assert_classpath_contents({
      self.set_default: False,
      self.set_managed: True,
      self.set_managed2: False,
    }, 'redundant')

  def test_forceful_fail(self):
    run = self._run_project('forceful', conflict_strategy='FAIL')
    self.assert_failure(run)

  def test_managed_forceful_use_managed(self):
    self._assert_classpath_contents({
      self.set_default: False,
      self.set_managed: True,
      self.set_managed2: False,
    }, 'forceful', conflict_strategy='USE_MANAGED')
