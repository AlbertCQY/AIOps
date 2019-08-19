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
#os info
os_data_ip = '1.1.3.200'
os_user = 'oracle'
os_pass = 'oracle22222'
# oracle connect info
ora_ip = '1.1.3.200'
ora_usr = 'sys'
ora_pass = 'bigbangdata.cn'
ora_port = 1521
ora_srvname = 'orcl'
#oracle directory info 
o_directory_name = 'soe_dir'
o_directory_path = '/oradata/soe_dir'
#base info 
ora_env = """
export ORACLE_BASE=/u01/app/oracle;
export ORACLE_HOME=$ORACLE_BASE/product/12.2.0/db_1;
export PATH=$ORACLE_HOME/bin:/usr/sbin:/usr/local/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/home/oracle/.local/bin:/home/oracle/bin;
export LD_LIBRARY_PATH=$ORACLE_HOME/lib:/lib:/usr/lib:/usr/locall/lib;
export CLASSPATH=$ORACLE_HOME/JRE:$ORACLE_HOME/jlib:$ORACLE_HOME/rdbms/jlib;
"""
#swingbench settings
list_user_count = [10,20,30,40,50,60,70,80,90,100]
swing_rt = '00:01'
dumpfile_dir = '/tools/deploy_dir'
dumpfiles = ['soe_01.dmp','soe_02.dmp','soe_03.dmp','soe_04.dmp','soe_05.dmp','soe_06.dmp']
tbs_total_size = 900
tbs_tmp_size = 120



