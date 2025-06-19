# timerfd 
    创建一个定时器，该定时器通过文件描述符来传递定时器过期通知，可以用select、poll、epoll来监听。

## 接口
``````C
#include <sys/timerfd.h>

int timerfd_create(int clockid, int flags);
int timerfd_settime(int fd, int flags,
                    const struct itimerspec *new_value,
                    struct itimerspec *_Nullable old_value);
int timerfd_gettime(int fd, struct itimerspec *curr_value);
``````

- timerfd_create
  - 参数
    - clockid:只能用一下的参数
      - CLOCK_REALTIME: 非单调递增时钟，会被系统时间调整(NTP & adjtime)影响(一般不用)
      - CLOCK_MONOTONIC:单调递增时钟，不可修改，但是会被adjtime和NTP影响，频率影响时间(一般使用)，对系统挂起不敏感
      - CLOCK_BOOTTIME:单调递增时钟,系统挂起也一直计时，但会被settimeofday活着类似函数修改BOOT TIME影响
      - CLOCK_REALTIME_ALARM & CLOCK_BOOTTIME_ALARM: 没用过，应用场景目前不存在系统挂起状态
    - flags:
      - linux 2.6.26之前只能设置为0
      - O_NONBLOCK:设置对select、poll、epoll没有影响，仅告诉调用者文件描述符是否就绪
      - TFD_CLOEXEC:多线程使用
- timerfd_settime
  - new_value.it_value非0启动定时器，0关闭定时器；new_value.it_interval超时周期
  - flags:0表示相对时间（软件 timer_id运行当前时间 + 启动时间new_value）,TFD_TIMER_ABSTIME 绝对时间，由设置的new_value值决定。
  - old_value:一般填写NULL，<mark>非NULL没研究过，没想道对应的应用场景</mark>

- 练习
  - 1s定时
``````C
#include <sys/timerfd.h>
#include <iostream>
#include <stdio.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <sys/poll.h>
#include <cassert>
#include <cstring>
#include <sys/types.h>
#include <sys/stat.h>
#include <thread>
int main(int argc, char *argv[]) {

    struct itimerspec tmo = {
            {1, 0},// 1s 定时
            {1, 0} //需要设置一个起始时间，全为0定时器不会启动，timerfd_settime第二个参数
                    // 设置0时，该时间是基于 当前时间 + tmo.it_value 启动的
    };

    int vsc_fd = timerfd_create(CLOCK_MONOTONIC, TFD_NONBLOCK | TFD_CLOEXEC);
    if (vsc_fd < 0) {
        printf("[%s][%d] timerfd_create errno:%d\n", __FUNCTION__, __LINE__, errno);
        return -1;
    }

    if (timerfd_settime(vsc_fd, 0, &tmo, NULL) < 0) {
        printf("[%s][%d] vsc timerfd_settime errno:%d", __FUNCTION__, __LINE__, errno);
        return -1;
    }

    struct pollfd fd = {vsc_fd, POLLIN, 0};
    char times[sizeof(uint64_t)];
    while (true) {
        int ret = poll(&fd, 1, -1);
        if (ret < 0) {
            printf("[%s][%d] poll errno:%d\n", __FUNCTION__, __LINE__, errno);
        } else {
            //两种方式触发定时
            //微妙级定时器
#if 0
            //方式1，读取过期数
            //不读取会一直有事件上报上来
            ret = read(fd.fd, times, sizeof(uint64_t));
            if (ret < 0) {
                printf("[%s][%d] read errno:%d\n", __FUNCTION__, __LINE__, errno);
            } else {
                struct timespec curTime{};
                clock_gettime(CLOCK_MONOTONIC, &curTime);
                printf("curTime: %ld.%09ld times:%ld\n", curTime.tv_sec, curTime.tv_nsec, *((uint64_t *)times));
            }
#elif 1
            //方式2，重新设置
            if (timerfd_settime(vsc_fd, 0, &tmo, NULL) < 0) {
                printf("[%s][%d] vsc timerfd_settime errno:%d", __FUNCTION__, __LINE__, errno);
                return -1;
            }
            struct timespec curTime{};
            clock_gettime(CLOCK_MONOTONIC, &curTime);
            printf("curTime: %ld.%09ld \n", curTime.tv_sec, curTime.tv_nsec);

#endif
            
        }
    }


    return 1;
}

``````
  - 指定未来某一时刻启动1s定时
    - 方式1：相对时间启动
    - 方式2: 绝对时间启动
``````C
#include <sys/timerfd.h>
#include <iostream>
#include <stdio.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <sys/poll.h>
#include <cassert>
#include <cstring>
#include <sys/types.h>
#include <sys/stat.h>
#include <thread>
// 相对
int main(int argc, char *argv[]) {

    struct itimerspec tmo = {
            {1, 0},// 1s 定时
            {10, 0} //需要设置一个起始时间，全为0定时器不会启动,timerfd_settime第二个参数
                    // 设置0时，该时间是基于 当前时间 + tmo.it_value 启动的
    };

    int vsc_fd = timerfd_create(CLOCK_MONOTONIC, TFD_NONBLOCK | TFD_CLOEXEC);
    if (vsc_fd < 0) {
        printf("[%s][%d] timerfd_create errno:%d\n", __FUNCTION__, __LINE__, errno);
        return -1;
    }

    struct timespec startTime{};
    clock_gettime(CLOCK_MONOTONIC, &startTime);
    printf("startTime: %ld.%09ld \n", startTime.tv_sec, startTime.tv_nsec);

    if (timerfd_settime(vsc_fd, 0, &tmo, NULL) < 0) {
        printf("[%s][%d] vsc timerfd_settime errno:%d", __FUNCTION__, __LINE__, errno);
        return -1;
    }
    struct pollfd fd = {vsc_fd, POLLIN, 0};
    char times[sizeof(uint64_t)];
    while (true) {
        int ret = poll(&fd, 1, -1);
        if (ret < 0) {
            printf("[%s][%d] poll errno:%d\n", __FUNCTION__, __LINE__, errno);
        } else {
            ret = read(fd.fd, times, sizeof(uint64_t));
            if (ret < 0) {
                printf("[%s][%d] read errno:%d\n", __FUNCTION__, __LINE__, errno);
            } else {
                struct timespec curTime{};
                clock_gettime(CLOCK_MONOTONIC, &curTime);
                printf("curTime: %ld.%09ld times:%ld\n", curTime.tv_sec, curTime.tv_nsec, *((uint64_t *)times));
            }
        }
    }
    return 1;
}
``````
``````C
#include <sys/timerfd.h>
#include <iostream>
#include <stdio.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <sys/poll.h>
#include <cassert>
#include <cstring>
#include <sys/types.h>
#include <sys/stat.h>
#include <thread>
//绝对
int main(int argc, char *argv[]) {

    struct itimerspec tmo = {
            {1, 0},// 1s 定时
            {1, 0} //需要设置一个起始时间，全为0定时器不会启动
    };

    int vsc_fd = timerfd_create(CLOCK_MONOTONIC, TFD_NONBLOCK | TFD_CLOEXEC);
    if (vsc_fd < 0) {
        printf("[%s][%d] timerfd_create errno:%d\n", __FUNCTION__, __LINE__, errno);
        return -1;
    }

    struct timespec startTime{};
    clock_gettime(CLOCK_MONOTONIC, &startTime);
    printf("startTime: %ld.%09ld \n", startTime.tv_sec, startTime.tv_nsec);
    tmo.it_value = startTime ;
    tmo.it_value.tv_sec += 10;

    if (timerfd_settime(vsc_fd, TFD_TIMER_ABSTIME, &tmo, NULL) < 0) {
        printf("[%s][%d] vsc timerfd_settime errno:%d", __FUNCTION__, __LINE__, errno);
        return -1;
    }
    struct pollfd fd = {vsc_fd, POLLIN, 0};
    char times[sizeof(uint64_t)];
    while (true) {
        int ret = poll(&fd, 1, -1);
        if (ret < 0) {
            printf("[%s][%d] poll errno:%d\n", __FUNCTION__, __LINE__, errno);
        } else {
            //两种方式触发定时
            //微妙级定时器
#if 1
            //方式1，读取过期数
            //不读取会一直有事件上报上来
            ret = read(fd.fd, times, sizeof(uint64_t));
            if (ret < 0) {
                printf("[%s][%d] read errno:%d\n", __FUNCTION__, __LINE__, errno);
            } else {
                struct timespec curTime{};
                clock_gettime(CLOCK_MONOTONIC, &curTime);
                printf("curTime: %ld.%09ld times:%ld\n", curTime.tv_sec, curTime.tv_nsec, *((uint64_t *)times));
            }
#elif 0
            //方式2，重新设置
            if (timerfd_settime(vsc_fd, 0, &tmo, NULL) < 0) {
                printf("[%s][%d] vsc timerfd_settime errno:%d", __FUNCTION__, __LINE__, errno);
                return -1;
            }
            struct timespec curTime{};
            clock_gettime(CLOCK_MONOTONIC, &curTime);
            printf("curTime: %ld.%09ld \n", curTime.tv_sec, curTime.tv_nsec);

#endif

        }
    }


    return 1;
}
``````


  - 只启动一次
``````C
#include <sys/timerfd.h>
#include <iostream>
#include <stdio.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <sys/poll.h>
#include <cassert>
#include <cstring>
#include <sys/types.h>
#include <sys/stat.h>
#include <thread>
int main(int argc, char *argv[]) {

    struct itimerspec tmo = {
            {0, 0},// 全为0，表示只启动一次
            {1, 0} //需要设置一个起始时间，全为0定时器不会启动
    };

    int vsc_fd = timerfd_create(CLOCK_MONOTONIC, TFD_NONBLOCK | TFD_CLOEXEC);
    if (vsc_fd < 0) {
        printf("[%s][%d] timerfd_create errno:%d\n", __FUNCTION__, __LINE__, errno);
        return -1;
    }

    struct timespec startTime{};
    clock_gettime(CLOCK_MONOTONIC, &startTime);
    printf("startTime: %ld.%09ld \n", startTime.tv_sec, startTime.tv_nsec);

    if (timerfd_settime(vsc_fd, 0, &tmo, NULL) < 0) {
        printf("[%s][%d] vsc timerfd_settime errno:%d", __FUNCTION__, __LINE__, errno);
        return -1;
    }
    struct pollfd fd = {vsc_fd, POLLIN, 0};
    char times[sizeof(uint64_t)];
    while (true) {
        int ret = poll(&fd, 1, -1);
        if (ret < 0) {
            printf("[%s][%d] poll errno:%d\n", __FUNCTION__, __LINE__, errno);
        } else {
            //两种方式触发定时
            //微妙级定时器
#if 1
            //方式1，读取过期数
            //不读取会一直有事件上报上来
            ret = read(fd.fd, times, sizeof(uint64_t));
            if (ret < 0) {
                printf("[%s][%d] read errno:%d\n", __FUNCTION__, __LINE__, errno);
            } else {
                struct timespec curTime{};
                clock_gettime(CLOCK_MONOTONIC, &curTime);
                printf("curTime: %ld.%09ld times:%ld\n", curTime.tv_sec, curTime.tv_nsec, *((uint64_t *)times));
            }
#elif 0
            //方式2，重新设置
            if (timerfd_settime(vsc_fd, 0, &tmo, NULL) < 0) {
                printf("[%s][%d] vsc timerfd_settime errno:%d", __FUNCTION__, __LINE__, errno);
                return -1;
            }
            struct timespec curTime{};
            clock_gettime(CLOCK_MONOTONIC, &curTime);
            printf("curTime: %ld.%09ld \n", curTime.tv_sec, curTime.tv_nsec);

#endif

        }
    }


    return 1;
}
``````

# 参考
[open](https://man7.org/linux/man-pages/man2/open.2.html)   
[time_create](https://man7.org/linux/man-pages/man2/timerfd_create.2.html)  
[time_settime](https://man7.org/linux/man-pages/man2/timer_settime.2.html)  