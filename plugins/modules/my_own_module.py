#!/usr/bin/python

DOCUMENTATION = r'''
---
module: my_own_module
short_description: Create a text file with the specified content
version_added: "1.0.0"
description:
  - Creates a UTF-8 text file or updates its content.
  - Leaves the file unchanged when its content already matches.
  - The parent directory must exist. Symbolic links are not supported.
options:
  path:
    description: Absolute or relative path to the text file.
    required: true
    type: path
  content:
    description: Exact text to write, without adding a newline.
    required: true
    type: str
attributes:
  check_mode:
    support: full
  diff_mode:
    support: full
author:
  - nevers0nn
'''

EXAMPLES = r'''
- name: Create a text file
  my_own_namespace.yandex_cloud_elk.my_own_module:
    path: /tmp/my_own_module
    content: "Hello from my module!\n"
'''

RETURN = r'''
path:
  description: Absolute path of the managed file.
  type: str
  returned: always
  sample: /tmp/my_own_module
'''

import os
import tempfile

from ansible.module_utils.basic import AnsibleModule


def run_module():
    module = AnsibleModule(
        argument_spec={
            'path': {'type': 'path', 'required': True},
            'content': {'type': 'str', 'required': True},
        },
        supports_check_mode=True,
    )
    path = os.path.abspath(module.params['path'])
    content = module.params['content']
    desired = content.encode('utf-8')
    current = None
    temporary_path = None

    try:
        if not os.path.isdir(os.path.dirname(path)):
            module.fail_json(msg='Parent directory does not exist', path=path)
        if os.path.lexists(path):
            if os.path.islink(path) or not os.path.isfile(path):
                module.fail_json(msg='Path must be a regular file', path=path)
            with open(path, 'rb') as existing:
                current = existing.read()

        result = {'changed': current != desired, 'path': path}
        if module._diff:
            result['diff'] = {
                'before_header': path,
                'after_header': path,
                'before': current.decode('utf-8', errors='replace') if current is not None else '',
                'after': content,
            }
        if not result['changed'] or module.check_mode:
            module.exit_json(**result)

        descriptor, temporary_path = tempfile.mkstemp(dir=module.tmpdir)
        with os.fdopen(descriptor, 'wb') as output:
            output.write(desired)
        module.atomic_move(temporary_path, path)
        temporary_path = None
        module.exit_json(**result)
    except OSError as error:
        module.fail_json(msg=str(error), path=path, changed=False)
    finally:
        if temporary_path is not None and os.path.exists(temporary_path):
            os.unlink(temporary_path)


def main():
    run_module()


if __name__ == '__main__':
    main()
