# 环境
    ubuntu20.04

# 生成多个ssh-key,并用指定ssh-key 访问git
1. 安装ssh-keygen
2. ssh-keygen -t rsa -C "xxx" -f /home/hf/.ssh/u_kernel_649
   note:非root用户，用户名是hf
3. 确认是否生成hf用户.ssh是否生成u_kernel_649.pub文件
   cd  /home/hf/.ssh/ && ls && cat u_kernel_649.pub
4. 将密钥拷贝到github分支上
   setting --> SSH and GPG keys --> new SSH key --> 自定义key 名，并将u_kernel_649.pub文件内容拷贝到key中

5. 配置.ssh config文件 & 访问
   1. touch config & chmod a+x config
   2. 增加如下  
    >Host kernel649
        HostName github.com
        PreferredAuthentications publickey
        IdentityFile ~/.ssh/u_kernel_649.pub        
    > Host 是别名
    3. ssh clone 分支       
        一般:git@github.com:hanfeng-zz/linux-test.git
        改为:git@kernel649:hanfeng-zz/linux-test.git
6. 结束