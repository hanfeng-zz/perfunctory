
# 总结

- pub/sub 即都可做server/client，pub节点仅发送，sub节点仅接收

- 如果pub节点connect成功后，立刻发送消息，前面几条消息会丢，具体和设备环境有关系

# 示例

## 单个pub/sub
    见下方

## 多pub,单sub

- client:pub-connect

```C
#include <zmq.h>
#include <cassert>
#include <iostream>
#include <netinet/in.h>
#include <spdlog/spdlog.h>
#define XTS_SWITCH_TOD_IPC "ipc:///tffs/pulsars/run/xts-test-1.ipc"
#define BUF_LEN 100

int main(int argc, char *argv[]) {
    assert(argc == 2);

    int send_cnt = 0;
    char send_buf[BUF_LEN] {};
    int *send_ptr = (int *)(send_buf + 1);

    send_buf[0] = std::stoi(argv[1]);

    auto context = zmq_ctx_new();
    assert(nullptr != context);

    auto publisher = zmq_socket(context, ZMQ_PUB);
    assert(nullptr != publisher);

    int rc = zmq_connect(publisher, XTS_SWITCH_TOD_IPC);
    assert(rc == 0);

    while(1) {
        *send_ptr = htonl(send_cnt);

        rc = zmq_send(publisher, send_buf, sizeof(send_cnt) + 1, 0);
        if (rc < 0) {
            std::cout << "[" << __FUNCTION__ << "][" << __LINE__ << "] send failed,errno:" << errno << std::endl;
        }

        std::cout << "[" << __FUNCTION__ << "][" << __LINE__ << "] send cnt:" << send_cnt << std::endl;
        ++send_cnt;

        sleep(1);
    }

    zmq_close(publisher);
    zmq_ctx_destroy(context);
    return 0;
}
```


- server:sub-bind

```C
#include <zmq.h>
#include <cassert>
#include <iomanip>
#include <iostream>
#include <spdlog/spdlog.h>
#define XTS_SWITCH_TOD_IPC "ipc:///tffs/pulsars/run/xts-test-1.ipc"
#define BUF_LEN 100

void msg_print(const int &len, const char *buf) {
    std::ostringstream oss {};
    oss << "len:" << len << " receive:\n";
    for (int j = 0; j < len; j++) {
        oss << std::setw(2) << std::setfill('0') << std::hex << (0xff & buf[j]) << " ";
    }
    std::cout << oss.str() << std::endl;
}

int main (void) {
    auto context = zmq_ctx_new();
    assert(nullptr != context);

    auto subscriber = zmq_socket(context, ZMQ_SUB);
    assert(nullptr != subscriber);

    int rc = zmq_bind(subscriber, XTS_SWITCH_TOD_IPC);
    assert(rc == 0);

    rc = zmq_setsockopt(subscriber, ZMQ_SUBSCRIBE, nullptr, 0);
    assert(rc == 0);

    zmq_pollitem_t zitem {};
    zitem.socket = subscriber;
    zitem.events = ZMQ_POLLIN;
    char recv[BUF_LEN];

    while (1) {
        rc = zmq_poll(&zitem, 1, -1);
        if (rc < 0) {
            std::cout << "[" << __FUNCTION__ << "][" << __LINE__ << "] send failed,errno:" << errno << std::endl;
            continue;
        }

        rc = zmq_recv(zitem.socket, recv, 100, 0);
        if (rc < 0) {
            spdlog::error("[{}][{}] recv failed,errno:{}", __FUNCTION__, __LINE__, errno);
            continue;
        }

        msg_print(rc, recv);
    }

    zmq_close(subscriber);
    zmq_ctx_destroy(context);
}
```