## swingbench使用
swingbench是oracle开发部门的一个废弃项目，目前是在oracle工作的一个哥们继续开发，不受oracle官方支持。 软件下载地址：http://www.dominicgiles.com/swingbench.html 可以下载到最新版本。
### swingbench安装&运行
a.需要java环境java1.6以上。
b.解压后直接运行bin目录下的oewizard造数据，造完数据后可以使用图形界面的swingbench或者命令行界面的charbench
**说明：** 造压测数据库必须使用oewizard图形工具，没有提供命令行工具
### 官方的命令行解释
自动压测脚本使用python调用swingbench的命令行工具，图形界面使用方式请参考官方文档，下面是以swingbench 2.5为例命令行说明：
```
./charbench -h
usage: parameters:
-D                use value for given environment variable    
-a                run automatically                                   
-be               end recording statistics after. Value is in  the form hh:mm                                      
-bg               indicate that charbench will be run in the  background                                          
-bs               start recording statistics after. Value is  in the form hh:mm                                   
-c                specify config file                                 
-co               specify/override coordinator in   configuration file.                                 
-com           	  specify comment for this benchmark run (in double quotes)                                      
-cpuloc        	  specify/overide location/hostname of the cpu monitor.                                        
-cpupass     	  specify/overide os password of the user    used to monitor cpu.                                
-cpuuser          specify/overide os username of the user   used to monitor cpu.                                
-cs               override connect string in configuration     file                                                
-debug            turn on debugging. Written to standard out          
-debugf           turn on debugging. Witten to debug.log.             
-debugfine        turn on finest level of debugging                   
-di               disable transactions(s) by short name,    comma separated                                     
-dt               override driver type in configuration file         (thin, oci, ttdirect, ttclient)                     
-dumptx           output transaction response times to file           
-dumptxdir        directory for transaction response times    files                                               
-en               enable transactions(s) by short name, comma     separated                                           
-env              display environment configuration                   
-g                distributed group identifier                        
-h,--help         print this message                                  
-i                run interactively (default)                         
-intermax         override minimum inter transaction sleep time (default = 0)                                  
-intermin         override minimum inter transaction sleep  time (default = 0)                                  
-ld               specify/overide the logon delay    (milliseconds)                                      
-max              override maximum intra transaction think     time in configuration file                          
-min              override minimum intra transaction think    time in configuration file                          
-p                override password in configuration file             
-r                specify results file                                
-rr               specify/overide refresh rate for charts in      secs                                                
-rt               specify/overide run time for the benchmark.     Value is in the form hh:mm                          
-s                run silent                                          
-u                override username in configuration file             
-uc               override user count in configuration file.          
-v                display run statistics (vmstat/sar like   output), options include (comma separated no spaces). 
                  trans|cpu|disk|dml|tpm|tps|users|resp|vresp         
-vo               output file for verbose output (defaults to  stdout)                                             
```
### swingbench测试脚本
设置不同的并发用户并限制运行时间为15分钟
```
/home/oracle/swingbench_2.5/bin/charbench -c test.xml -cs //192.168.244.229/test -uc 200 -rt 00:15 -dt thin -a -v users,tpm,tps,cpu,disk > oltp_swingbench_raidtest_200.txt
/home/oracle/swingbench_2.5/bin/charbench -c test.xml -cs //192.168.244.229/test -uc 500 -rt 00:15 -dt thin -a -v users,tpm,tps,cpu,disk > oltp_swingbench_raidtest_500.txt
/home/oracle/swingbench_2.5/bin/charbench -c test.xml -cs //192.168.244.229/test -uc 1000 -rt 00:15 -dt thin -a -v users,tpm,tps,cpu,disk > oltp_swingbench_raidtest_1000.txt
/home/oracle/swingbench_2.5/bin/charbench -c test.xml -cs //192.168.244.229/test -uc 1500 -rt 00:15 -dt thin -a -v users,tpm,tps,cpu,disk > oltp_swingbench_raidtest_1500.txt
/home/oracle/swingbench_2.5/bin/charbench -c test.xml -cs //192.168.244.229/test -uc 2000 -rt 00:15 -dt thin -a -v users,tpm,tps,cpu,disk > oltp_swingbench_raidtest_2000.txt
```
### 故障小排除
**故障现象：**
在oewizard工具造数的时候，发现数据库可以正常连接，但是创建完用户和表空间后，开始并发插入数据的时候，发现报java异常的错误，部分错误如下： ORA-12516：TNS:listener could not find available handler with matching protocol stack 意思是java的连接池不够用了，申请不到连接，所以异常了。
**解决方法：**
 数据库的process参数值设置太小了，默认的150，按照oewizard设置的并发数适当的调大就可以了。
## 自动压测脚本
**github地址:**
https://github.com/AlbertCQY/AIOps/tree/master/otps_test
### 准备操作
**Oracle数据库操作(压测数据库)**
造好压测数据后，需要把测试数据以dmp文件的格式导出来，方便多次使用
```
expdp \'sys/bigbangdata.cn@1.1.3.111:1521/orcl12c as sysdba\' schemas=soe directory=soe_dir dumpfile=soe_%U.dmp logfile=soe_expdp.log parallel=6 compression=all
```
**Mysql数据库操作(压测资料库)**
```
创建数据库:
create database otpstest DEFAULT CHARSET=utf8;
创建表:
CREATE TABLE otpstest.`t_history` (
  `ID` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `DBINFO` varchar(100) NOT NULL DEFAULT '' COMMENT '数据库业务名信息，比如鉴权库',
  `IPINFO` varchar(100) NOT NULL DEFAULT '' COMMENT '连接数据库的IP地址',
  `BEGIN_TIME` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '测试开始时间',
  `END_TIME` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '测试结束时间',
  `USERS` varchar(200) NOT NULL DEFAULT '' COMMENT '压测连接的用户数',
  `MAX_TPS` bigint(20) unsigned NOT NULL COMMENT '最大TPS值',
  `MIN_TPS` bigint(20) unsigned NOT NULL COMMENT '最小TPS值',
  `AVG_TPS` bigint(20) unsigned NOT NULL COMMENT '平均TPS值',
  `USER_CPU` bigint(20) unsigned NOT NULL COMMENT '最大TPS时USER_CPU值',
  `SYSTEM_CPU` bigint(20) unsigned NOT NULL COMMENT '最大TPS时SYSTEM_CPU值',
  `WAIT_CPU` bigint(20) unsigned NOT NULL COMMENT '最大TPS时WAIT_CPU值',
  `IDLE_CPU` bigint(20) unsigned NOT NULL COMMENT 'I最大TPS时DLE_CPU值',
  `BI_IO` bigint(20) unsigned NOT NULL COMMENT '最大TPS时BI_IO',
  `BO_IO` bigint(20) unsigned NOT NULL COMMENT '最大TPS时BO_IO',
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='TPS汇总信息表';

CREATE TABLE otpstest.`t_tmp` (
  `ID` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `DBINFO` varchar(100) NOT NULL DEFAULT '' COMMENT '数据库业务名信息，比如鉴权库',
  `IPINFO` varchar(100) NOT NULL DEFAULT '' COMMENT '连接数据库的IP地址',
  `TPS_TIME` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '测试的时间',
  `USERS` varchar(200) NOT NULL DEFAULT '' COMMENT '压测连接的用户数',
  `TPM` bigint(20) unsigned NOT NULL COMMENT 'TPM值',
  `TPS` bigint(20) unsigned NOT NULL COMMENT 'TPS值',
  `USER_CPU` bigint(20) unsigned NOT NULL COMMENT 'USER_CPU值',
  `SYSTEM_CPU` bigint(20) unsigned NOT NULL COMMENT 'SYSTEM_CPU值',
  `WAIT_CPU` bigint(20) unsigned NOT NULL COMMENT 'WAIT_CPU值',
  `IDLE_CPU` bigint(20) unsigned NOT NULL COMMENT 'IDLE_CPU值',
  `BI_IO` bigint(20) unsigned NOT NULL COMMENT 'BI_IO',
  `BO_IO` bigint(20) unsigned NOT NULL COMMENT 'BO_IO',
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='临时信息表';

CREATE TABLE otpstest.`t_history_detail` (
  `ID` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `DBINFO` varchar(100) NOT NULL DEFAULT '' COMMENT '数据库业务名信息，比如鉴权库',
  `IPINFO` varchar(100) NOT NULL DEFAULT '' COMMENT '连接数据库的IP地址',
  `TPS_TIME` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '测试的时间',
  `USERS` varchar(200) NOT NULL DEFAULT '' COMMENT '压测连接的用户数',
  `TPM` bigint(20) unsigned NOT NULL COMMENT 'TPM值',
  `TPS` bigint(20) unsigned NOT NULL COMMENT 'TPS值',
  `USER_CPU` bigint(20) unsigned NOT NULL COMMENT 'USER_CPU值',
  `SYSTEM_CPU` bigint(20) unsigned NOT NULL COMMENT 'SYSTEM_CPU值',
  `WAIT_CPU` bigint(20) unsigned NOT NULL COMMENT 'WAIT_CPU值',
  `IDLE_CPU` bigint(20) unsigned NOT NULL COMMENT 'IDLE_CPU值',
  `BI_IO` bigint(20) unsigned NOT NULL COMMENT 'BI_IO',
  `BO_IO` bigint(20) unsigned NOT NULL COMMENT 'BO_IO',
  PRIMARY KEY (`ID`),
  KEY IDX_TPS_TIME (`TPS_TIME`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='详细压测历史信息表';
```
### 脚本使用
**使用帮助：**
只支持python3环境
```
python3 main.py -h
usage: main.py [-h] [-run RUN]

Oracle Swingbench Tps Test Tool

optional arguments:
  -h, --help  show this help message and exit
  -run RUN    输入importdata开始导入soe的数据&&输入tpstest开始压测
```
python3 main.py -run importdata   #往待压测oracle数据库中导入测试数据
python3 main.py -run tpstest   #开始压测，压测信息需要在settings.py文件中设置
**settings.py配置文件**
```
#!/usr/bin/env python
# -*- coding:utf-8 -*-
#business name
db_info = 'testdb'
# mysql connect info
my_ip = '1.1.3.111'
my_usr = 'compare'
my_pass = 'ZAQ_xsw2'
my_port = 3306
my_db = 'otpstest'
#os info,待压测数据库主机信息
os_data_ip = '1.1.3.200'
os_user = 'oracle'
os_pass = 'oracle22222'
# oracle connect info，待压测数据库信息
ora_ip = '1.1.3.200'
ora_usr = 'sys'
ora_pass = 'bigbangdata.cn'
ora_port = 1521
ora_srvname = 'orcl'
#oracle directory info 
o_directory_name = 'soe_dir'
o_directory_path = '/oradata/soe_dir'
#base info ，待压测数据库oracle环境变量信息
ora_env = """
export ORACLE_BASE=/u01/app/oracle;
export ORACLE_HOME=$ORACLE_BASE/product/12.2.0/db_1;
export PATH=$ORACLE_HOME/bin:/usr/sbin:/usr/local/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/home/oracle/.local/bin:/home/oracle/bin;
export LD_LIBRARY_PATH=$ORACLE_HOME/lib:/lib:/usr/lib:/usr/locall/lib;
export CLASSPATH=$ORACLE_HOME/JRE:$ORACLE_HOME/jlib:$ORACLE_HOME/rdbms/jlib;
"""
#swingbench settings
list_user_count = [10,20,30,40,50,60,70,80,90,100]  #设置的压测并发用户数，会按照此列表来循环压测
swing_rt = '00:15'   #每次压测时间为15分钟
dumpfile_dir = '/tools/deploy_dir'   #存放dmp文件位置，压测服务器上存放
dumpfiles = ['soe_01.dmp','soe_02.dmp','soe_03.dmp','soe_04.dmp','soe_05.dmp','soe_06.dmp']  #expdp压测数据后，产生的oracle dmp文件
tbs_total_size = 900  #importdata时，预扩容soe表空间的大小
tbs_tmp_size = 120  #importdata时，预扩容临时表空间的大小
```
