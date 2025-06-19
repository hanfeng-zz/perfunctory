
# push-pull 总结

 * 1、管道模式
 * 2、push节点支持zmq_send，不支持zmq_recv，pull节点相反
 * 3、zmq_send是block模式，
 *    即在send buffer未充满的情况下，数据保存在buffer中，直到buffer充满，
 *    buffer的长度是1000数据(与数据内容无关，测试过4byte，34byte数据包，都是达到1000条就不再发送了)，
 *    buffer充满后，如果zmq_send没设置超时，就会被阻塞，直到有pull节点接收数据，push节点才会继续发送，如果设置超时，后续数据会被丢弃，并提示errno:11 Resource temporarily unavailable;
 * 4、push/pull即可以做server节点，也可以做client节点,一对一情况下
 * 5、可以多个push-client节点，单个pull-server节点,不可以多个push-server节点，单个pull-client节点，因为第一个push-server节点占用了IPC通道，后续server绑定成功，但是在发送的时候会提示errno:11 Resource temporarily unavailable

#
# 示例

## 1、一个服务端push, 一个客户端pull


- <mark> 服务端push
```C
#include <zmq.h>
#include <cassert>
#include <spdlog/spdlog.h>
#include <netinet/in.h>

#define XTS_SWITCH_TOD_IPC4 "ipc:///tffs/pulsars/run/xts-test-4.ipc"

int main() {
    int rc, cnt = 0, tmo = 1;
    char buf[100] {};

    int *ptr = (int *)(buf);

    auto context = zmq_ctx_new();
    assert(nullptr != context);

    auto push = zmq_socket(context, ZMQ_PUSH);
    assert(nullptr != push);

    rc = zmq_bind(push, XTS_SWITCH_TOD_IPC4);
    assert(rc == 0);

    while (1) {
        *ptr = htonl(cnt);

        rc = zmq_send(push, buf, sizeof(int) + 1, 0);
        if (rc < 0) {
            spdlog::error("[{}][{}] send failed,errno:{}", __FUNCTION__, __LINE__, errno);
        }

        spdlog::info("[{}][{}] push send:{}", __FUNCTION__, __LINE__, cnt);
        cnt++;
        sleep(1);
    }

    zmq_close(push);
    zmq_ctx_destroy(context);
    return 0;
}
```

- <mark>客户端pull
```C
#include <zmq.h>
#include <cassert>
#include <spdlog/spdlog.h>
#define XTS_SWITCH_TOD_IPC4 "ipc:///tffs/pulsars/run/xts-test-4.ipc"

int main() {
    int rc;
    auto context = zmq_ctx_new();
    assert(nullptr != context);

    auto pull = zmq_socket(context, ZMQ_PULL);
    assert(nullptr != pull);

    rc = zmq_connect(pull, XTS_SWITCH_TOD_IPC4);
    assert(rc == 0);

    zmq_pollitem_t item = {.socket = pull, .fd = 0, .events = ZMQ_POLLIN,.revents = 0,};

    char buf[100];

    while (1) {
        rc = zmq_poll(&item, 1, -1);
        if (rc < 0) {
            spdlog::error("[{}][{}] poll failed,errno:{}", __FUNCTION__, __LINE__, errno);
        } else {
            if (item.revents & ZMQ_POLLIN) {
                rc = zmq_recv(item.socket, buf, 100, 0);
                if (rc < 0) {
                    spdlog::error("[{}][{}] recv failed,errno:{}", __FUNCTION__, __LINE__, errno);
                } else {
                    for (int j = 0; j < rc; j++) {
                        printf("%02x ", buf[j]);
                    }
                    printf("\n");
                }
            }
        }
    }

    zmq_close(pull);
    zmq_ctx_destroy(context);
    return 0;
}

```

## 2、一个服务端pull，一个客户端push

* 见3

## 3、一个服务端pull，多个客户端push

- <mark>客户端，多节点push

```C
#include <zmq.h>
#include <cassert>
#include <spdlog/spdlog.h>
#include <netinet/in.h>

#define XTS_SWITCH_TOD_IPC4 "ipc:///tffs/pulsars/run/xts-test-4.ipc"


int main(int argc, char *argv[]) {
    assert(argc == 2);

    int rc, cnt = 0;
    int opt_val = 0;
    size_t opt_len = sizeof (int);//note:官方文档提供的是int64_t,但是实际环境使用int,具体原因就不查了，应该和操作系统+zmq版本有关系
    char buf[100] {};

    buf[0] = std::stoi(argv[1]);//note:第一个字节用于表示哪个程序
    spdlog::info("[{}][{}] process number:{}", __FUNCTION__, __LINE__, buf[0]);

    int *ptr = (int *)(buf + 1);

    auto context = zmq_ctx_new();
    assert(nullptr != context);

    auto push = zmq_socket(context, ZMQ_PUSH);
    assert(nullptr != push);

    rc = zmq_connect(push, XTS_SWITCH_TOD_IPC4);
    assert(rc == 0);

    rc = zmq_getsockopt(push, ZMQ_SNDBUF, &opt_val, &opt_len);
    assert(rc == 0);
    spdlog::info("[{}][{}] push socket len:{}", __FUNCTION__, __LINE__, opt_val);

    while (1) {
        *ptr = htonl(cnt);

        rc = zmq_send(push, buf, sizeof(int) + 1, 0);
        if (rc < 0) {
            spdlog::error("[{}][{}] send failed,errno:{}", __FUNCTION__, __LINE__, errno);
        }

        spdlog::info("[{}][{}] push send:{}", __FUNCTION__, __LINE__, cnt);
        cnt++;
        sleep(1);
    }

    zmq_close(push);
    zmq_ctx_destroy(context);
    return 0;
}
```


- <mark>服务端：单节点pull

```C
#include <zmq.h>
#include <cassert>
#include <spdlog/spdlog.h>
#define XTS_SWITCH_TOD_IPC4 "ipc:///tffs/pulsars/run/xts-test-4.ipc"

int main() {
    int rc;
    auto context = zmq_ctx_new();
    assert(nullptr != context);

    auto pull = zmq_socket(context, ZMQ_PULL);
    assert(nullptr != pull);

    rc = zmq_bind(pull, XTS_SWITCH_TOD_IPC4);
    assert(rc == 0);

    zmq_pollitem_t item = {.socket = pull, .fd = 0, .events = ZMQ_POLLIN,.revents = 0,};

    char buf[100];

    while (1) {
        rc = zmq_poll(&item, 1, -1);
        if (rc < 0) {
            spdlog::error("[{}][{}] poll failed,errno:{}", __FUNCTION__, __LINE__, errno);
        } else {
            if (item.revents & ZMQ_POLLIN) {
                rc = zmq_recv(item.socket, buf, 100, 0);
                if (rc < 0) {
                    spdlog::error("[{}][{}] recv failed,errno:{}", __FUNCTION__, __LINE__, errno);
                } else {
                    for (int j = 0; j < rc; j++) {
                        printf("%02x ", buf[j]);
                    }
                    printf("\n");
                }
            }
        }
    }

    zmq_close(pull);
    zmq_ctx_destroy(context);
    return 0;
}

```