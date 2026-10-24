#define _GNU_SOURCE

#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

static int signal_children(int signal_number)
{
    char path[80];
    FILE *children;
    long child;

    snprintf(path, sizeof(path), "/proc/self/task/%ld/children", (long)getpid());
    children = fopen(path, "re");
    if (children == NULL)
        return -1;

    /* We are single-threaded and do not reap during this scan, so these child
     * PIDs cannot be reused before kill(). When a parent exits, its remaining
     * descendants are adopted by this subreaper and reached on the next pass.
     * This includes processes that used setsid() or changed process groups. */
    while (fscanf(children, "%ld", &child) == 1) {
        if (child > 0)
            (void)kill((pid_t)child, signal_number);
    }
    if (ferror(children)) {
        fclose(children);
        return -1;
    }
    return fclose(children);
}

static long long monotonic_ms(void)
{
    struct timespec now;

    if (clock_gettime(CLOCK_MONOTONIC, &now) < 0)
        return -1;
    return (long long)now.tv_sec * 1000 + now.tv_nsec / 1000000;
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
    int stop_signal = 0;
    long long stop_deadline = 0;
    sigset_t signals;
    sigset_t original_mask;
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
    sigemptyset(&signals);
    sigaddset(&signals, SIGCHLD);
    sigaddset(&signals, SIGHUP);
    sigaddset(&signals, SIGINT);
    sigaddset(&signals, SIGQUIT);
    sigaddset(&signals, SIGTERM);
    /* Block before fork so stop requests and child exits cannot be lost
     * between checking children and waiting for the next signal. */
    if (sigprocmask(SIG_BLOCK, &signals, &original_mask) < 0
            || prctl(PR_SET_NAME, "reaper", 0, 0, 0) < 0
            || prctl(PR_SET_CHILD_SUBREAPER, 1, 0, 0, 0) < 0
            || signal_children(0) < 0) {
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
        if (sigprocmask(SIG_SETMASK, &original_mask, NULL) < 0)
            _exit(126);
        execvp(command[0], command);
        fprintf(stderr, "reaper: could not start %s: %s\n",
                command[0], strerror(errno));
        _exit(errno == ENOENT ? 127 : 126);
    }

    (void)setpgid(child, child);
    for (;;) {
        int status;
        int received;
        pid_t waited;

        while ((waited = waitpid(-1, &status, WNOHANG)) > 0) {
            if (waited == child)
                child_status = status;
        }
        if (waited < 0) {
            if (errno == EINTR)
                continue;
            if (errno == ECHILD)
                break;
            fprintf(stderr, "reaper: wait failed: %s\n", strerror(errno));
            return 1;
        }

        if (stop_signal != 0) {
            const struct timespec interval = {.tv_sec = 0, .tv_nsec = 100000000};
            long long now = monotonic_ms();
            int forwarded = now < 0 || now >= stop_deadline ? SIGKILL : stop_signal;

            if (signal_children(forwarded) < 0) {
                fprintf(stderr, "reaper: could not signal children: %s\n", strerror(errno));
                return 1;
            }
            received = sigtimedwait(&signals, NULL, &interval);
        } else {
            received = sigwaitinfo(&signals, NULL);
        }
        if (received < 0) {
            if (errno == EINTR || errno == EAGAIN)
                continue;
            fprintf(stderr, "reaper: signal wait failed: %s\n", strerror(errno));
            return 1;
        }
        if (received != SIGCHLD && stop_signal == 0) {
            stop_signal = received;
            stop_deadline = monotonic_ms() + 2000;
        }
    }
    return stop_signal != 0 ? 128 + stop_signal : exit_status(child_status);
}
