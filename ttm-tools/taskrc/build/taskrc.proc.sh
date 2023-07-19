#!/bin/sh

tmp_file=tmp.1.taskrc_proc.cpp
tmp_file_2=tmp.2.taskrc_proc.cpp

alias log_debug=echo

function cpp_transform_pre()
{
  for cur_input_cpp in $@
  do
    # log_debug "running pre $cur_input_cpp"
    cat $cur_input_cpp > $tmp_file

    # preserve spacing
    cat $tmp_file | sed 's|  | +++ |g' > $tmp_file_2 && mv $tmp_file_2 $tmp_file
    cat $tmp_file | sed 's|+++ |+++-|g' > $tmp_file_2 && mv $tmp_file_2 $tmp_file

    # preserve comments
    cat $tmp_file | sed 's|//|!!|g' > $tmp_file_2 && mv $tmp_file_2 $tmp_file

    # update input
    cat $tmp_file > $cur_input_cpp

    # remove temporary files
    rm $tmp_file
  done
}

function cpp_transform_post()
{
  input_cpp="$1"

  for cur_input_cpp in $@
  do
    # log_debug "running post $cur_input_cpp"
    cat $cur_input_cpp > $tmp_file

    # restore comments as original
    cat $tmp_file | sed 's|!!|#|g' > $tmp_file_2 && mv $tmp_file_2 $tmp_file

    # restore spacing
    cat $tmp_file | sed 's|+++-|+++ |g' > $tmp_file_2 && mv $tmp_file_2 $tmp_file
    cat $tmp_file | sed 's| +++ |  |g' > $tmp_file_2 && mv $tmp_file_2 $tmp_file

    # collapse all entries of form A, B, C to A,B,C
    cat $tmp_file | sed 's|, *|,|g' > $tmp_file_2 && mv $tmp_file_2 $tmp_file

    # update input
    cat $tmp_file > $cur_input_cpp

    # remove temporary files
    rm $tmp_file
  done

}

function taskrc_proc() {
  input_cpp="$1"
  output_tmp=taskrc_proc.output.cpp

  cpp_transform_pre *.cpp

  # run cpp preproc so that macros can be evaluated
  gcc -E -traditional-cpp $input_cpp | grep -v "^#" > $output_tmp

  cpp_transform_post *.cpp

  cat $output_tmp

  # remove temporary files
  rm $output_tmp
}
