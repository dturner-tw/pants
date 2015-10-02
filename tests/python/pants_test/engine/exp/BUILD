# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

python_tests(
  name='addressable',
  sources=['test_addressable.py'],
  dependencies=[
    'src/python/pants/engine/exp:addressable',
  ]
)


python_tests(
  name='graph',
  sources=['test_graph.py'],
  dependencies=[
    'src/python/pants/base:address',
    'src/python/pants/engine/exp:graph',
    'src/python/pants/engine/exp:parsers',
    'src/python/pants/engine/exp:targets',
  ]
)

python_tests(
  name='mapper',
  sources=['test_mapper.py'],
  dependencies=[
    'src/python/pants/base:address',
    'src/python/pants/engine/exp:mapper',
    'src/python/pants/engine/exp:parsers',
    'src/python/pants/util:contextutil',
  ]
)

python_tests(
  name='parsers',
  sources=['test_parsers.py'],
  dependencies=[
    'src/python/pants/engine/exp:parsers',
  ]
)

python_tests(
  name='targets',
  sources=['test_targets.py'],
  dependencies=[
    'src/python/pants/base:address',
    'src/python/pants/engine/exp:objects',
    'src/python/pants/engine/exp:targets',
  ]
)