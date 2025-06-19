# ubuntu 20.04 环境设置问题

## ch341-uart ttyUSB0 不被识别
- ubuntu 20.04 中ch341.ko太老
  - [ch341x-下载链接](https://www.wch.cn/download/CH341SER_LINUX_ZIP.html)
  - 放入Ubuntu后，unzip解压，并执行sudo make install 
- brltty进程占用了串口
  - sudo apt autoremove brltty
- 拔插串口，重新识别设备

## lib
  - sudo apt-get install libncurses5-dev
  - sudo apt-get install lzop
  - sudo apt-get install build-essential

## yyloc

  - /usr/bin/ld: scripts/dtc/dtc-parser.tab.o:(.bss+0x50): multiple definition of `yylloc'; scripts/dtc/dtc-lexer.lex.o:(.bss+0x0): first defined here
  - 解决：修改scripts/dtc目录下的dtc-lexer.lex.c_shipped文件中找到YYLTYPE yyloc这一行，在640行，在之前面加上extern

# gun binutils
[链接](https://sourceware.org/binutils/)

# uboot

## 语法 & uboot
  [uboot-record](https://elinux.org/Boot_Loaders#U-Boot)

## 基础知识

  ### nand和emmc的区别

  [参考链接](https://zhuanlan.zhihu.com/p/132387921)

  ### norflash、nandflash 区别

  ### sram 和sdram区别

  ### ROM 和RAM
  
  > RAM:random access memory,随机存取存储器一般称为（运行内存）
   ROM:read-only memory,只读存储器，一般使用于Bios，早期的ROM是技术原因出厂就不可更改，但是在ROM的基础上出现EPROM和 > EEPROM，这两种可擦写，又在此基础上发展出nand flash,然后是emmc
  >

  [参考链接](https://cn.bing.com/search?pglt=41&q=nand+flash+%E5%92%8Cesmc&cvid=5b998dddc4b645929f2b5f446a48c13d&aqs=edge..69i57j0l8.6663j0j1&FORM=ANAB01&PC=CNNDDB)


## linker script 

[参考链接](http://sourceware.org/binutils/docs/ld/Scripts.html#Scripts)

  - 3.1  <mark> todo: 看完需整理 </mark>
    - output file 和 each input file 被称为object file format 
    - output file 常被称为executable（可执行文件），purpose（<mark>暂时不好翻译</mark>）被称为object file ，每个object file有 章节列表（a lsit of sections），a section 在input file中称为input section，在output file中称为output section
    - 每个section在object file中有name 和 size，大部分还有相关联的数据块（an associated block of data）,统称为section contents；一个节可以被标记为loadable（加载到内存）或者allocatable（预留空间）或者两者都不是（debug info）
    - loadable 和allocatable 输出节点有两个地址 VMA，LMA，大部分情况二者地址是相同的
      - VMA：virtual memory address
      - LMA: load memory address
    - <mark>如何查看???</mark>
  - 3.2 linker script format
    - linker scripts是文本文件
    - 注释用/**/；空格被忽略；.....
  - 3.3 simple linker script example

  - 命令？？？
  - 各个文件夹下的lds内容又是什么？
  