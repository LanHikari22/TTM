#!/bin/bash

pushd ~/src/scripts/termdownscr

function run_test() {
  echo "======================================================================="
  echo "running $1"
  $(echo python3 -m $*)
}

run_test termdownscr.common
run_test termdownscr.lib
run_test termdownscr.termdown-parse-tmp unittest
run_test termdownscr.termdown-resume unittest

popd
