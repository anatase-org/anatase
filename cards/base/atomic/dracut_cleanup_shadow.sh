#!/bin/bash

check() {
    return 0
}

depends() {
    echo systemd-sysusers
}

install() {
    if [[ -f "$initdir/etc/shadow" ]]; then
        # Drop last-change value which is based on date
        sed -i 's/^\([^:]*:[^:]*:\)[0-9][0-9]*/\1/' "$initdir/etc/shadow"
    fi
}
