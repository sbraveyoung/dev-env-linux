#!/usr/bin/env bash

source ./functions.sh

printf2stdout "xxx" "xxx: %s\n" "hello world"
printf2stdout "quiet" "quiet: %s\n" "hello world"
printf2stdout "trace" "trace: %s\n" "hello world"
printf2stdout "debug" "debug: %s\n" "hello world"
printf2stdout "verbose" "verbose: %s\n" "hello world"
printf2stdout "info" "info: %s\n" "hello world"
printf2stdout "warning" "warning: %s\n" "hello world"
printf2stdout "error" "error: %s\n" "hello world"
set +e
(printf2stdout "fatal" "fatal: %s\n" "hello world")
(printf2stdout "panic" "panic: %s\n" "hello world")
