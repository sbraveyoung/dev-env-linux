#!/usr/bin/expect
set argv_index 3
set host    [lindex $argv 0]
set user    [lindex $argv 1]
set passwd  [lindex $argv 2]
set relay   [lindex $argv 3]
set timeout 10

puts $relay

if { $relay != "" } {
    spawn kinit
    expect {
        "*Password for*" { 
            send "$passwd\r";
        }
    }
    spawn ssh $relay
    expect {
        "*relay_server*" { send "$host\r" }
    }
} else {
    spawn ssh -l $user $host
    expect {
        "*Password*" { send "$passwd\r" }
        "*Last login*" {}
    }
}

interact
