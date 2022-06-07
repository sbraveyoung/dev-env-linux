#!/usr/bin/expect
set host    [lindex $argv 0]
set user    [lindex $argv 1]
set passwd  [lindex $argv 2]
set relay   [lindex $argv 3]
set timeout 10

if { $relay != "-" } {
    spawn kinit
    expect {
        "*Password for*" { 
            send "$passwd\r";
        }
    }
    spawn ssh $relay
    expect {
        "*relay_server$*" { send "$host\r" }
    }
} else {
    # spawn ssh -l $user $host
    spawn ssh -t $user@$host [lrange $argv 4 end]
    expect {
        "*Are you sure you want to continue connecting (yes/no/*" {
            send "yes\r"
            expect {
                "*\[Pp\]assword*" { send "$passed\r" }
            }
        }
        "*\[Pp\]assword*" { send "$passwd\r" }
        "*" {}
    }
}

interact
