"""
Module that contains the command line app.

Why does this file exist, and why not put this in __main__?

  You might be tempted to import things from __main__ later, but that will cause
  problems: the code will get executed twice:

  - When you run `python -mdualmon` python will execute
    ``__main__.py`` as a script. That means there won't be any
    ``dualmon.__main__`` in ``sys.modules``.
  - When you import __main__ it will get executed again (as a module) because
    there's no ``dualmon.__main__`` in ``sys.modules``.

  Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""
import argparse
from argparse import RawTextHelpFormatter
from subprocess import Popen, PIPE
PLACE_SECONDARY = 'right-of'    # default value

def run_cmd(cmd, **kwargs):
    p = Popen(cmd, stdout=PIPE, stderr=PIPE, **kwargs)
    out, err = p.communicate()
    return out.decode(), err.decode()

def read_xrandr():
    return run_cmd('xrandr')[0]

def get_connected_screens(xrandr_output):
    screens = []
    for line in xrandr_output.splitlines():
        if ' connected' in line:
            screens.append(line.split()[0])
            # print('Found screen:', screens[-1])
    return screens

def parse_args(screens):
    parser = argparse.ArgumentParser(epilog=make_epilog(), formatter_class=RawTextHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-l", "--left",
        help="secondary monitors are to the left of primary",
        action="store_true",
    )
    group.add_argument(
        "-r", "--right",
        help="secondary monitors are to the right of primary",
        action="store_true",
    )
    parser.add_argument(
        '-p', '--primary',
        help='set primary monitor',
        choices=screens)
    parser.add_argument(
        '-o', '--off',
        help="turn off non-primary monitors",
        action="store_true",
    )
    args = parser.parse_args()
    return args

def make_epilog():
    import edider
    mons = edider.get_monitors()
    mtxts = ['Monitor info:']
    for mon in mons:
        mtupl = mon.output_name, mon.name, mon.width_in_pixels, mon.height_in_pixels
        mtxt = '{}\t{}\t{}x{}'.format(*mtupl)
        mtxts.append(mtxt)
    return '\n'.join(mtxts)


def make_cmd(screens, args):
    placement = PLACE_SECONDARY
    for key in ('left', 'right'):
        if args.__dict__[key]:
            placement = key + '-of'
            print('Placement explicitly set to: {}-of'.format(placement))
            break

    total_cmd = ['xrandr']
    primary = args.primary
    if primary:
        screens.pop(screens.index(primary))
        screens.insert(0, primary)
        print('Using explicitly given primary monitor: {}'.format(screens[0]))
    else:
        print('Using default primary monitor: {}'.format(screens[0]))

    if args.off:
        for screen in screens[1:]:
            total_cmd.extend(['--output', screen, '--off'])
        return total_cmd
    for i, screen in enumerate(screens):
        opts = '--output {} --auto'.format(screen)
        if not i == 0:
            opts += ' --{} {}'.format(placement, screens[i-1])
        if primary == screen:
            opts += ' --primary'
        total_cmd.extend(opts.split())
    return total_cmd


def main(args=None):
    screens = get_connected_screens(read_xrandr())
    args = parse_args(screens)
    cmd = make_cmd(screens, args)
    # print(*cmd)
    run_cmd(cmd)
