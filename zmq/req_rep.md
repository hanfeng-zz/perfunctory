
# 总结

- req-rep 比较耗时，req节点执行顺序为send->receive, rep节点执行顺序为receive->send,一问一答方式避免消息遗漏，且注意这两个节点都是block模式，未设置send/recv timeout都是一直等待直到发送/接收成功.
  
- req/rep 在一个client/server模式下即可以做server，也可以做client；但多client一个server模式下,server端需设置ZMQ_REP-BIND，client端设置ZMQ_REQ-CONNECT。
  
  - client可以connect同一个地址，server只bind一个地址，server端zmq可以区分不同client并进行一对一回复(<mark>细节参考https://rfc.zeromq.org/spec/28/</mark>)，应用层需要自己设置标识进行区分哪个client的消息。

  - client connect不同地址，server可以重复绑定不同地址，地址类型不同，如同时绑定ipc和tcp
  
- 需要设置ZMQ_LINGER参数，避免关闭套接字后无限等待，程序退出不了。

- 该组合是同步模型

# 示例

## 一、一个req-client,一个rep-server(直连)

    见二

## 二、多个req-client,一个rep-server(直连-IPC方式)

* client节点:req-connect
```C
#include <iostream>
#include <zmq.h>
#include <cassert>
#include <spdlog/spdlog.h>
#include <sstream>
#include <iomanip>
#include <netinet/in.h>
#define XTS_SWITCH_TOD_IPC3 "ipc:///tffs/pulsars/run/xts-test-3.ipc"
#define BUF_LEN 100


void msg_print(const int &len, const char *buf) {
    std::ostringstream oss {};
    oss << "len:" << len << " receive:\n";
    for (int j = 0; j < len; j++) {
        oss << std::setw(2) << std::setfill('0') << std::hex << (0xff & buf[j]) << " ";
    }
    std::cout << oss.str() << std::endl;
}

int main(int argc, char *argv[]) {
    assert(argc == 2);//note: 第二个参数填数字表示rep编号

    int rc, send_cnt = 0;
    char send[BUF_LEN] {}, recv[BUF_LEN] {};
    int *send_ptr = (int *)(send + 1);

    send[0] = std::stoi(argv[1]);

    auto context = zmq_ctx_new();
    assert(nullptr != context);

    auto req = zmq_socket(context, ZMQ_REQ);
    assert(nullptr != req);

    rc = zmq_connect(req, XTS_SWITCH_TOD_IPC3);
    assert(rc == 0);

    while (1) {
        *send_ptr = htonl(send_cnt);
        rc = zmq_send(req, send, sizeof(int) + 1, 0);
        if (rc < 0) {
            std::cout << "[" << __FUNCTION__ << "][" << __LINE__ << "] send failed,errno:" << errno << std::endl;
        }

        std::cout << "[" << __FUNCTION__ << "][" << __LINE__ << "] send cnt:" << send_cnt << std::endl;
        ++send_cnt;

        rc = zmq_recv(req, recv, BUF_LEN, 0);
        if (rc < 0) {
            std::cout << "[" << __FUNCTION__ << "][" << __LINE__ << "] send failed,errno:" << errno << std::endl;
        }

        msg_print(rc, recv);

        sleep(1);
    }
   return 0;
}
```

* server节点：rep-bind
  
```C

#include <zmq.h>
#include <cassert>
#include <spdlog/spdlog.h>
#include <netinet/in.h>
#include <iostream>
#include <sstream>
#include <iomanip>
#define BUF_LEN 100
#define XTS_SWITCH_TOD_IPC3 "ipc:///tffs/pulsars/run/xts-test-3.ipc"

void msg_print(const int &len, const char *buf) {
    std::ostringstream oss {};
    oss << "len:" << len << " receive:\n";
    for (int j = 0; j < len; j++) {
        oss << std::setw(2) << std::setfill('0') << std::hex << (0xff & buf[j]) << " ";
    }
    std::cout << oss.str() << std::endl;
}

int main(int argc, char *argv[]) {
    assert(argc == 2);//note: 第二个参数填数字表示rep编号

    int rc, send_cnt = 0;
    char recv[BUF_LEN] {}, send[BUF_LEN] {};
    int *send_ptr = (int *)(send + 1);

    send[0] = std::stoi(argv[1]);

    auto context = zmq_ctx_new();
    assert(nullptr != context);

    auto rep = zmq_socket(context, ZMQ_REP);
    assert(nullptr != rep);

    rc = zmq_bind(rep, XTS_SWITCH_TOD_IPC3);
    assert(rc == 0);

    zmq_pollitem_t item = {
            .socket = rep,
            .fd = 0,
            .events = ZMQ_POLLIN,
            .revents = 0
    };

    while (true) {
        rc = zmq_poll(&item, 1, -1);
        if (rc < 0) {
            std::cout << "[" << __FUNCTION__ << "][" << __LINE__ << "] zmq failed,errno:" << errno << std::endl;

        } else {
            if (item.revents & ZMQ_POLLERR) {
                std::cout << "[" << __FUNCTION__ << "][" << __LINE__ << "] zmq error,errno:" << errno << std::endl;
            }

            if (item.revents & ZMQ_POLLIN) {
                rc = zmq_recv(rep, recv, BUF_LEN, 0);
                if (rc == -1) {
                    std::cout << "[" << __FUNCTION__ << "][" << __LINE__ << "] send failed,errno:" << errno << std::endl;
                    continue;
                }

                msg_print(rc, recv);

                *send_ptr = htonl(send_cnt);

                rc = zmq_send(rep, send, sizeof(send_cnt) + 1, 0);
                if (rc == -1) {
                    std::cout << "[" << __FUNCTION__ << "][" << __LINE__ << "] send failed,errno:" << errno << std::endl;
                } else {
                    std::cout << "[" << __FUNCTION__ << "][" << __LINE__ << "] send cnt:" << send_cnt << std::endl;
                }

                send_cnt++;
            }
        }
    }
    return 0;
}
```

## 多client，地址分别为IPC和TCP，单server同时绑定TCP/IPC地址

- server节点:rep-bind

```C
#include <zmq.h>
#include <cassert>
#include <spdlog/spdlog.h>
#include <netinet/in.h>
#include <iostream>
#include <sstream>
#include <iomanip>
#define BUF_LEN 100
#define XTS_SWITCH_TOD_IPC3 "ipc:///tffs/pulsars/run/xts-test-3.ipc"
#define XTS_SWITCH_TOD_IPC2 "ipc:///tffs/pulsars/run/xts-test-2.ipc"
#define XTS_SWITCH_TCP "tcp://eth1.x1:30000"
#define XTS_SWITCH_TCP1 "tcp://eth1.x1:20000"

void msg_print(const int &len, const char *buf) {
    std::ostringstream oss {};
    oss << "len:" << len << " receive:\n";
    for (int j = 0; j < len; j++) {
        oss << std::setw(2) << std::setfill('0') << std::hex << (0xff & buf[j]) << " ";
    }
    std::cout << oss.str() << std::endl;
}

int main(int argc, char *argv[]) {
    assert(argc == 2);//note: 第二个参数填数字表示rep编号

    int rc, send_cnt = 0;
    char recv[BUF_LEN] {}, send[BUF_LEN] {};
    int *send_ptr = (int *)(send + 1);

    send[0] = std::stoi(argv[1]);

    auto context = zmq_ctx_new();
    assert(nullptr != context);

    auto rep = zmq_socket(context, ZMQ_REP);
    assert(nullptr != rep);

    rc = zmq_bind(rep, XTS_SWITCH_TOD_IPC3);//绑定IPC
    assert(rc == 0);

    rc = zmq_bind(rep, XTS_SWITCH_TCP);//绑定TCP端口
    assert(rc == 0);

    zmq_pollitem_t item = {
            .socket = rep,
            .fd = 0,
            .events = ZMQ_POLLIN,
            .revents = 0
    };

    while (true) {
        rc = zmq_poll(&item, 1, -1);
        if (rc < 0) {
            std::cout << "[" << __FUNCTION__ << "][" << __LINE__ << "] zmq failed,errno:" << errno << std::endl;

        } else {
            if (item.revents & ZMQ_POLLERR) {
                std::cout << "[" << __FUNCTION__ << "][" << __LINE__ << "] zmq error,errno:" << errno << std::endl;
            }

            if (item.revents & ZMQ_POLLIN) {
                rc = zmq_recv(rep, recv, BUF_LEN, 0);
                if (rc == -1) {
                    std::cout << "[" << __FUNCTION__ << "][" << __LINE__ << "] send failed,errno:" << errno << std::endl;
                    continue;
                }

                msg_print(rc, recv);

                *send_ptr = htonl(send_cnt);

                rc = zmq_send(rep, send, sizeof(send_cnt) + 1, 0);
                if (rc == -1) {
                    std::cout << "[" << __FUNCTION__ << "][" << __LINE__ << "] send failed,errno:" << errno << std::endl;
                } else {
                    std::cout << "[" << __FUNCTION__ << "][" << __LINE__ << "] send cnt:" << send_cnt << std::endl;
                }

                send_cnt++;
            }
        }
    }
    return 0;
}
```


- client: req-connect

```C
#include <iostream>
#include <zmq.h>
#include <cassert>
#include <spdlog/spdlog.h>
#include <sstream>
#include <iomanip>
#include <netinet/in.h>
#define XTS_SWITCH_TOD_IPC3 "ipc:///tffs/pulsars/run/xts-test-3.ipc"
#define XTS_SWITCH_TOD_IPC2 "ipc:///tffs/pulsars/run/xts-test-2.ipc"
#define XTS_SWITCH_TCP "tcp://eth1.x1:0;246.0.12.12:30000"
#define XTS_SWITCH_TCP1 "tcp://eth1.x1:0;246.0.12.12:20000"
#define BUF_LEN 100


void msg_print(const int &len, const char *buf) {
    std::ostringstream oss {};
    oss << "len:" << len << " receive:\n";
    for (int j = 0; j < len; j++) {
        oss << std::setw(2) << std::setfill('0') << std::hex << (0xff & buf[j]) << " ";
    }
    std::cout << oss.str() << std::endl;
}

int main(int argc, char *argv[]) {
    assert(argc == 2);//note: 第二个参数填数字表示rep编号

    int rc, send_cnt = 0;
    char send[BUF_LEN] {}, recv[BUF_LEN] {};
    int *send_ptr = (int *)(send + 1);

    send[0] = std::stoi(argv[1]);

    auto context = zmq_ctx_new();
    assert(nullptr != context);

    auto req = zmq_socket(context, ZMQ_REQ);
    assert(nullptr != req);

    rc = zmq_connect(req, XTS_SWITCH_TCP); //根据需要替换IPC or tcp 地址
    assert(rc == 0);

    while (1) {
        *send_ptr = htonl(send_cnt);
        rc = zmq_send(req, send, sizeof(int) + 1, 0);
        if (rc < 0) {
            std::cout << "[" << __FUNCTION__ << "][" << __LINE__ << "] send failed,errno:" << errno << std::endl;
        }

        std::cout << "[" << __FUNCTION__ << "][" << __LINE__ << "] send cnt:" << send_cnt << std::endl;
        ++send_cnt;

        rc = zmq_recv(req, recv, BUF_LEN, 0);
        if (rc < 0) {
            std::cout << "[" << __FUNCTION__ << "][" << __LINE__ << "] send failed,errno:" << errno << std::endl;
        }

        msg_print(rc, recv);

        sleep(1);
    }

    return 0;
}
```