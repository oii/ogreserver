from __future__ import absolute_import
from __future__ import unicode_literals

import os


def test_setup_install(virtualenv):
    # locate python binary in venv
    venv_bin_python = os.path.join(virtualenv.path, 'bin', 'python')

    # change into ogreclient directory from project root
    os.chdir(os.path.join(os.getcwd(), 'ogreclient'))

    # install ogreclient; exception raised if this fails in virtualenvapi
    virtualenv._execute([venv_bin_python, 'setup.py', 'install'])
