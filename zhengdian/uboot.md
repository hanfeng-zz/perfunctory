# uboot 环境变量

# 使能 debug 开关
    在老的uboot中，include/common.h 中增加 #define DEBUG
>   ：结果如下      
>   #define DEBUG       
    #ifdef DEBUG        
    #define _DEBUG	1       
    #else       
    #define _DEBUG	0       
    #endif
>

[参考1](https://zhuanlan.zhihu.com/p/373505974)