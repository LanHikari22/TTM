#!/bin/bash

source taskrc.proc.sh

pushd ../build

# make sure we have up to date content
cp ../src/* .

# preprocess taskrc
taskrc_proc taskrc.cpp > taskrc && cat taskrc

# update system
cp taskrc ~/.taskrc

popd
