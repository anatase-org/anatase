#define _GNU_SOURCE

#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

static volatile sig_atomic_t child_group = -1;

static void forward_signal(int signal_number)
{
    pid_t group = (pid_t)child_group;

    if (group > 0)
        (void)kill(-group, signal_number);
}

static int install_signal_handlers(void)
{
    const int signals[] = {SIGHUP, SIGINT, SIGQUIT, SIGTERM};
    struct sigaction action;
    size_t index;

    memset(&action, 0, sizeof(action));
    action.sa_handler = forward_signal;
    sigemptyset(&action.sa_mask);
    for (index = 0; index < sizeof(signals) / sizeof(signals[0]); index++) {
        if (sigaction(signals[index], &action, NULL) < 0)
            return -1;
    }
    return 0;
}

static int exit_status(int status)
{
    if (WIFEXITED(status))
        return WEXITSTATUS(status);
    if (WIFSIGNALED(status))
        return 128 + WTERMSIG(status);
    return 1;
}

int main(int argc, char **argv)
{
    char **command = NULL;
    pid_t child;
    int child_status = 1 << 8;
    int index;

    for (index = 1; index < argc; index++) {
        if (strcmp(argv[index], "--") == 0) {
            command = &argv[index + 1];
            break;
        }
    }
    if (command == NULL || command[0] == NULL) {
        fprintf(stderr, "reaper: expected a command after --\n");
        return 2;
    }
    if (prctl(PR_SET_NAME, "reaper", 0, 0, 0) < 0
            || prctl(PR_SET_CHILD_SUBREAPER, 1, 0, 0, 0) < 0
            || install_signal_handlers() < 0) {
        fprintf(stderr, "reaper: initialization failed: %s\n", strerror(errno));
        return 1;
    }

    child = fork();
    if (child < 0) {
        fprintf(stderr, "reaper: fork failed: %s\n", strerror(errno));
        return 1;
    }
    if (child == 0) {
        (void)setpgid(0, 0);
        execvp(command[0], command);
        fprintf(stderr, "reaper: could not start %s: %s\n",
                command[0], strerror(errno));
        _exit(errno == ENOENT ? 127 : 126);
    }

    (void)setpgid(child, child);
    child_group = child;
    for (;;) {
        int status;
        pid_t waited = waitpid(-1, &status, 0);

        if (waited < 0) {
            if (errno == EINTR)
                continue;
            if (errno == ECHILD)
                break;
            fprintf(stderr, "reaper: wait failed: %s\n", strerror(errno));
            return 1;
        }
        if (waited == child)
            child_status = status;
    }
    child_group = -1;
    return exit_status(child_status);
}
