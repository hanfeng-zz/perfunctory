# POLLERR、POLLIN 同时上报
## 目的
- 使用poll机制监听虚拟网卡（tun/tap设备）和物理网卡
- 设置events poller触发事件类型: POLLIN & POLLPRI
- 监听数据

## 问题
&emsp;&emsp;监听过程中，revent不停的有POLLERR事件产生

## 分析&定位

### 1、报文错误     
>&emsp;&emsp;关闭所有模块的报文发送，保证网卡没有报文传输，问题依旧存在

### 2、文件描述符错误   
>&emsp;&emsp;确认无误后，问题依旧存在

### 3、重新回顾POLLERR定义

> POLLERR    
&emsp;&emsp;Error condition (only returned in revents; ignored in events).  This bit is also set for a file descriptor referring to the write end of a pipe when the read end has been closed.  
> https://man7.org/linux/man-pages/man2/poll.2.html
>&emsp;&emsp;表示POLLERR不被events触发，有且未读到完整数据，因为写管道被关闭，会触发；   
&emsp;&emsp;但是实际情况不是这样的，因为没有任何数据往网卡写；      

>其它工程师回答：    
&emsp;&emsp;1、POLLERR意味着socket出现异步错误（具体不太懂）; file descriptor 不支持polling    
https://stackoverflow.com/questions/24791625/how-to-handle-the-linux-socket-revents-pollerr-pollhup-and-pollnval

### 4、重新查看所有网卡的revent，物理网卡和虚拟网卡不同，只有虚拟网卡有POLLERR  
&emsp;&emsp;发现虚拟网卡(虚拟网卡默认是关闭的，软件架构原因)和物理网卡的区别在于没有running，使用 ifconfig eth1.1 up后，该网卡POLLERR告警消失

### 5、为什么网卡的down会引发error？
&emsp;&emsp;<mark>查看内核
>
> &emsp;&emsp;由于该设备是在这里仅用于以太二层，所以先查看内核tap.c文件（根据下图C代码）,只有获取到数据内容为空的时候，才会返回POOLERR，但这里的空不仅仅是stream还可能包括其它（不熟悉VFS架构，暂时搞不清楚，推测是网卡（tap）设备的down状态引发poll机制，但同时没有数据上发上来）
> 
```C
static __poll_t tap_poll(struct file *file, poll_table *wait)
{
	struct tap_queue *q = file->private_data;
	__poll_t mask = EPOLLERR;

	if (!q)
		goto out;

	mask = 0;
	poll_wait(file, &q->sock.wq.wait, wait);

	if (!ptr_ring_empty(&q->ring))
		mask |= EPOLLIN | EPOLLRDNORM;

	if (sock_writeable(&q->sk) ||
	    (!test_and_set_bit(SOCKWQ_ASYNC_NOSPACE, &q->sock.flags) &&
	     sock_writeable(&q->sk)))
		mask |= EPOLLOUT | EPOLLWRNORM;

out:
	return mask;
}       
```
> &emsp;&emsp;查看tun.c文件,有两种的情况会触发PLLERR;   
> &emsp;&emsp;1、无数据     
> &emsp;&emsp;2、网络设备探测未成功【直译】
```C
/* Poll */
static __poll_t tun_chr_poll(struct file *file, poll_table *wait)
{
	struct tun_file *tfile = file->private_data;
	struct tun_struct *tun = tun_get(tfile);
	struct sock *sk;
	__poll_t mask = 0;

	if (!tun)
		return EPOLLERR;

	sk = tfile->socket.sk;

	poll_wait(file, sk_sleep(sk), wait);

	if (!ptr_ring_empty(&tfile->tx_ring))
		mask |= EPOLLIN | EPOLLRDNORM;

	/* Make sure SOCKWQ_ASYNC_NOSPACE is set if not writable to
	 * guarantee EPOLLOUT to be raised by either here or
	 * tun_sock_write_space(). Then process could get notification
	 * after it writes to a down device and meets -EIO.
	 */
	if (tun_sock_writeable(tun, tfile) ||
	    (!test_and_set_bit(SOCKWQ_ASYNC_NOSPACE, &sk->sk_socket->flags) &&
	     tun_sock_writeable(tun, tfile)))
		mask |= EPOLLOUT | EPOLLWRNORM;

	if (tun->dev->reg_state != NETREG_REGISTERED)
		mask = EPOLLERR;

	tun_put(tun);
	return mask;
}
```
> 综上所述，还是网卡的down状态触发了poll上报机制；在其它书中看到过这样的描述:
>> “注意，fwide 并不改变已定向流的定向。还应注意的是，fwide 无出错返回。试想，如若流是无效>>的，那么将发生什么呢？我们唯一可依靠的是，<mark>在调用 fwide 前先清除 errno，从fwide返>>回时检查errno的值.
>>
><mark>所以可以侧面判定出需要清除这个error，才有可能不会有POLLERR上报;如下
```C++
ret = getsockopt(_fd.fd, SOL_SOCKET, SO_ERROR, &opt_val, &optlen);
```
> <mark>读完错误后就没有POLLERR上报了。

# 参考
[stackOverflow_1](https://stackoverflow.com/questions/24791625/how-to-handle-the-linux-socket-revents-pollerr-pollhup-and-pollnval) 

[poll_manual](https://man7.org/linux/man-pages/man2/poll.2.html)

[CSDN](https://blog.csdn.net/pingglala/article/details/37911083)

[tcpdump](https://github.com/the-tcpdump-group/libpcap/issues/899)