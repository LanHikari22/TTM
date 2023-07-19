#! /bin/sh

# Argument Parsing -----------------------------------------------------------
PARSE_ARGS_PY=$(cat <<- EOM
import argparse
import sys
import json

sys.argv[0] = 'release'

p = argparse.ArgumentParser(description='Installs files from this repository',
    formatter_class=argparse.RawDescriptionHelpFormatter)

p.add_argument('-v', '--verbose', action='count', default=0,
               help='increase output verbosity (default: %(default)s)')
p.add_argument('-o', '--output', default='$HOME/.task/',
               help='Path to copy files')
p.add_argument('-b', '--binoutput', default='$HOME/.local/bin/',
               help='Path to copy binary files in bin/ to')
p.add_argument('--args', action='store_true',
               help='Returns passed arguments as json')

p.add_argument('--taskrc', action='store_true',
               help='Copy taskrc over')
p.add_argument('--all', action='store_true',
               help='Copy all optional or first-time as well.')

#  p.add_argument('required_positional_arg',
               #  help='desc')
#  p.add_argument('required_int', type=int,
               #  help='req number')
#  p.add_argument('--on', action='store_true',
               #  help='include to enable')

args = p.parse_args()
print(json.dumps(args.__dict__))
exit(99)
EOM
)

args_json=$(python3 -c "$PARSE_ARGS_PY" $@)
args_status=$?
#echo $(echo $args_json | jq -r .verbose)

if [ $args_status -eq 0 ]; then # display help
  echo "$args_json"
  exit 0
elif [ $args_status -ne 99 ]; then # error parsing args
  exit 2
fi
# ----------------------------------------------------------------------------

if [ $(echo $args_json | jq -r .args) = true ]; then
  echo $args_json
  exit 0
fi

verbose=$(echo $args_json | jq -r .verbose)
output=$(echo $args_json | jq -r .output)
binoutput=$(echo $args_json | jq -r .binoutput)

log_debug()
{
  if [ $verbose -gt 1 ]; then
    echo $@
  fi
}

cpv()
{
  if [ $verbose -gt 0 ]; then
    cp --verbose $@
    echo
    :
  else
    cp $@
    :
  fi
}

cpv bin/* $binoutput
cpv hooks/* $output/hooks/
if [ $(echo $args_json | jq -r .all) = true ]; then
  cpv -r taskrc $output/
else
  if [ $(echo $args_json | jq -r .taskrc) = true ]; then
    cpv -r taskrc $output/
  fi
fi
