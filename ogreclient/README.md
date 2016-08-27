===== Distributing Ogreclient =====

==== Simple ====

Run the following command:

  make dist


==== Detailed ====

The normal Python setuptools method will create a source distribution that is cross-platform compatible.
The actual command for this is in the `Makefile`, as part of the `dist` command.

=== OSX ===





==== Testing ====

The dist directory contains two Vagrant projects, one for OSX and one for Windows. These enable us
to test the client install scripts on each client OS.
