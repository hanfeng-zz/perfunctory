# uboot

# 实验

# 创建、删除新板卡，根据NXP的uboot 代码
1. 
   - cd include/configs/
   - cp mx6ullevk.h mx6ullevk_zhaozheng.h
   - 
  
2. 
   - cd configs
   - cp mx6ull_14x14_evk_nand_defconfig mx6ull_14x14_evk_nand_zhaozheng_defconfig 
   - 修改后内容，改动部分含zhaozheng
  > 1. CONFIG_SYS_EXTRA_OPTIONS="IMX_CONFIG=board/> freescale/mx6ullevk/imximage.cfg,zhaozheng_test"
  >  2. CONFIG_ARM=y
  >  3. CONFIG_ARCH_MX6=y
  >  4. CONFIG_TARGET_MX6ULL_14X14_EVK_ZHAOZHENG=y
  >  5. CONFIG_CMD_GPIO=y

1. 1
   - cd board/freescale/
   - cp mx6ullevk/ -r mx6ullevk_zhaozheng
   - cd mx6ullevk_zhaozheng/
   - mv mx6ullevk.c mx6ullevk_zhaozheng.c
   - 修改Makefile
    ``` C
      obj-y  := mx6ullevk_zhaozheng.o
      extra-$(CONFIG_USE_PLUGIN) :=  plugin.bin
      $(obj)/plugin.bin: $(obj)/plugin.o
	  $(OBJCOPY) -O binary --gap-fill 0xff $< $@ 
      ```
   - 修改imximage.cfg
    ``` C
    修改第36行，文件路径
    PLUGIN	board/freescale/mx6ullevk_zhaozheng/plugin.bin 0x00907000
    ```
    - 修改Kconfig
    ``````C 
    if TARGET_MX6ULL_14X14_EVK_ZHAOZHENG

    config SYS_BOARD
        default "mx6ullevk_zhaozheng"

    config SYS_VENDOR
        default "freescale"

    config SYS_CONFIG_NAME
        default "mx6ullevk_zhaozheng"

    config SYS_SOC
        default "mx6"
    endif

    ``````
    - 修改MAINTAINERS
    ``````
    MX6ULLEVK_ZHAOZHENG BOARD
    M:	Peng Fan <peng.fan@nxp.com>
    S:	Maintained
    F:	board/freescale/mx6ullevk_zhaozheng/
    F:	include/configs/mx6ullevk_zhaozheng.h
    F:	configs/mx6ull_14x14_evk_nand_zhaozheng_defconfig
    ``````

    - 修改uboot 图形配置界面
   ``````C
   增加内容如下
   config TARGET_MX6ULL_14X14_EVK_ZHAOZHENG
        bool "Support mx6ull_14x14_evk_zhaozheng"
        select MX6ULL
        select DM
        select DM_THERMAL
    source "board/freescale/mx6ullevk_zhaozheng/Kconfig"    
    ``````
    
   
   

# 随记
1. 在uboot中make menuconfig xxx_defconfig 可以替换成make menuconfig xxx_config
   
2. CONFIG_SYS_EXTRA_OPTIONS     
   后续uboot会被取消掉，见doc/README.kconfig

# 问题
1. Warning - bad CRC, using default environment     
   - env default -a
   - saveenv 
   - 重启uboot

2. include/config、include/configs、configs目录的区别<mark> [待确认]</mark>        
    历史原因，configs目录下都是xxx_defconfig文件，是标准kconfig定义，但是还是有些c 头文件存在（include/config、include/configs），在后续解决；见doc/README.kconfig.
   
3. <mark>什么是MTD？？？</mark>