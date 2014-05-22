import sys

def debug_print(*args, **kwargs):
    for o in args:
        sys.stdout.write('{}\n'.format(o))
    sys.stdout.flush()
