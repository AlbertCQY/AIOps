#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import subprocess
from datetime import datetime
import sys
import os
import re
import argparse
from prettytable import PrettyTable
import settings
import RemoteSsh
from connect_mysql import Mysql_Conn
from connect_oracle import Oracle_Conn
def f_getlist(file_name='/tmp/a.txt'):
    list_file= open(file_name, "r")
    try:
        filelist = list_file.readlines()
    finally:
        list_file.close()
    list_return_detail=[]
    for rowinfo in filelist:
        if not rowinfo[0].isdigit(): #删除空行信息
            pass
        else:
            rowinfo =  re.sub(' +', ' ', rowinfo) #把每一行中间多个空格替换为一个空格
            rowinfo = rowinfo.replace('\t',' ')
            rowinfo = rowinfo.strip()
            list_row = rowinfo.split(' ') #把每一行转换为列表
            list_return_detail.append(list_row)
    return list_return_detail
# def cmd(command):
#     subp = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=655360, encoding="utf-8")
#     subp.wait(900)
#     if subp.poll() == 0:
#         print(subp.communicate()[1])
#     else:
#         print("执行失败")
def ImportData():
    #建立ssh连接
    ssh = RemoteSsh.SSHManager(settings.os_data_ip,settings.os_user,settings.os_pass)
    #base info
    sql_sum_tbs = """select sum(case when MAXBYTES=0 then bytes else MAXBYTES end)/1024/1024/1024 tbs_size from dba_data_files where TABLESPACE_NAME='SOE'"""
    sql_sum_tmptbs = """select sum(case when MAXBYTES=0 then bytes else MAXBYTES end)/1024/1024/1024 tmptbs_size from dba_temp_files where TABLESPACE_NAME='TEMP'"""
    sql_q_dir = """select directory_path from dba_directories where DIRECTORY_NAME = upper('{0}')"""
    sql_q_usr = """select username from dba_users where username='SOE'"""
    sql_c_tbs = ''
    sql_add_file = ''
    sql_add_tmpfile = ''
    if settings.tbs_total_size <=30:
        sql_c_tbs = 'create tablespace soe datafile size 5g'
        sql_add_file = 'alter tablespace soe add datafile size 5g'
    elif settings.tbs_total_size >30:
        sql_c_tbs = 'create tablespace soe datafile size 30g'
        sql_add_file = 'alter tablespace soe add datafile size 30g'
    if settings.tbs_tmp_size <=30:
        sql_add_tmpfile = 'alter tablespace temp add tempfile size 5g'
    elif settings.tbs_tmp_size >30:
        sql_add_tmpfile = 'alter tablespace temp add tempfile size 30g'

    #创建到oracle的连接
    o_conn=Oracle_Conn(settings.ora_usr,settings.ora_pass,settings.ora_ip,settings.ora_port,settings.ora_srvname)
    res_tbs = o_conn.execsql(sql_sum_tbs)
    res_tmptbs = o_conn.execsql(sql_sum_tmptbs)
    res_o_dir = o_conn.execsql(sql_q_dir.format(settings.o_directory_name))
    res_o_usr = o_conn.execsql(sql_q_usr)
    res_osdir = ssh.ssh_exec_cmd('ls {0}'.format(settings.o_directory_path))
    #print(res_o_dir[0][0],settings.o_directory_path)
    #校验directory_name和directory_path，上传dump文件
    if res_o_dir:
        pass
    else:
        print('oracle目录',settings.o_directory_name,'不存在')
        sys.exit()
    if res_o_dir[0][0] == settings.o_directory_path: 
        if 'No such file or directory' not in res_osdir:#检查后OS中存在此目录
            # if 'soe_01.dmp' in res_osdir and 'soe_02.dmp' in res_osdir and 'soe_03.dmp' in res_osdir and 'soe_04.dmp' in res_osdir and 'soe_05.dmp' in res_osdir and 'soe_06.dmp' in res_osdir:
            #     pass
            file_exists = True
            for f1 in settings.dumpfiles:
                if f1 not in res_osdir:
                    file_exists = False
            if file_exists is True:
                pass
            else:
                for f2 in settings.dumpfiles:
                    ssh._upload_file(settings.dumpfile_dir+'/'+f2, settings.o_directory_path + '/'+ f2)
        else:
            print(res_osdir,'检查目录后请重新配置')
            sys.exit()
    else:
        print('settings文件中o_directory_name和o_directory_path不对应，检查后重新配置')
        sys.exit()
    #处理soe表空间,如果没有则新建soe tbs，如果发现表空间空间太小，则扩容
    #print(res_tbs)
    if res_tbs[0][0] == None:
        print(sql_c_tbs)
        o_conn.execsql(sql_c_tbs)
        res_size = o_conn.execsql(sql_sum_tbs)
        res_size = res_size[0][0]
        while res_size < settings.tbs_total_size:
            print(sql_add_file)
            o_conn.execsql(sql_add_file)
            res_tbs1 = o_conn.execsql(sql_sum_tbs)
            res_size = res_tbs1[0][0]
    else:
        tbs_size = res_tbs[0][0]
        while tbs_size < settings.tbs_total_size:
            print(sql_add_file)
            o_conn.execsql(sql_add_file)
            res_tbs1 = o_conn.execsql(sql_sum_tbs)
            tbs_size = res_tbs1[0][0]
    #扩容temp表空间
    tmptbs_size = res_tmptbs[0][0]
    while tmptbs_size < settings.tbs_tmp_size:
        print(sql_add_tmpfile)
        o_conn.execsql(sql_add_tmpfile)
        res_tbs2 = o_conn.execsql(sql_sum_tmptbs)
        tmptbs_size = res_tbs2[0][0]
    #导入soe用户
    if res_o_usr:
        print('oracle soe 用户已存在，检查并清理后再重试')
        pass #也可以直接退出
    else:
        cmd_impdp = ''
        if settings.ora_usr == 'sys':
            cmd_impdp = """impdp \\'{ora_usr}/{ora_pass}@{ora_ip}:{ora_port}/{ora_srvname} as sysdba\\' schemas=soe directory={o_directory_name} cluster=n dumpfile=soe_soe_960g_%U.dmp logfile=soe_impdp.log parallel=8 JOB_NAME=impdp_soe""".format(
            ora_usr = settings.ora_usr,ora_pass=settings.ora_pass,ora_ip=settings.ora_ip,ora_port=settings.ora_port,ora_srvname=settings.ora_srvname,o_directory_name=settings.o_directory_name)
        else:
            cmd_impdp = """impdp {ora_usr}/{ora_pass}@{ora_ip}:{ora_port}/{ora_srvname}  schemas=soe directory={o_directory_name} cluster=n dumpfile=soe_soe_960g_%U.dmp logfile=soe_impdp.log parallel=8 JOB_NAME=impdp_soe""".format(
            ora_usr = settings.ora_usr,ora_pass=settings.ora_pass,ora_ip=settings.ora_ip,ora_port=settings.ora_port,ora_srvname=settings.ora_srvname,o_directory_name=settings.o_directory_name)
        print('开始导入用户持续时间较长...\n'+cmd_impdp)
        res_imp = ssh.ssh_exec_cmd(settings.ora_env+cmd_impdp)
        txt_success = """Job "{0}"."IMPDP_SOE" successfully completed""".format(settings.ora_usr.upper())
        if txt_success in res_imp:
            print('soe用户导入成功\n',ssh.ssh_exec_cmd("""tail -10 {0}/soe_impdp.log""".format(settings.o_directory_path)))
        else:
            print('soe用户导入失败\n',res_imp,ssh.ssh_exec_cmd("""tail -20 {0}/soe_impdp.log""".format(settings.o_directory_path)))

def OltpTest():
    #创建到mysql的连接
    m_conn=Mysql_Conn(settings.my_usr,settings.my_pass,settings.my_ip,settings.my_port,settings.my_db)
    cmd_swingbench = """/tools/swingbench/bin/charbench -c /tools/swingbench/bin/swingconfig.xml -cs //{ora_ip}:{ora_port}/{ora_srv} -cpuloc {ora_ip} -cpuuser {host_user} -cpupass {host_pass} -uc {user_count} -rt {rt} -dt thin -a -v users,tpm,tps,cpu,disk""".format(
        ora_ip = settings.ora_ip,ora_port=settings.ora_port,ora_srv = settings.ora_srvname,host_user=settings.os_user,host_pass=settings.os_pass.replace('$','\$'),user_count='{user_count}',rt = settings.swing_rt)
    list_dic_final = []
    for i in settings.list_user_count:
        exec_swing = cmd_swingbench.format(user_count = i)+' > /tmp/result_'+str(i)
        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"),'开始'+str(i)+'个并发用户压测......\n',exec_swing)
        subprocess.run(exec_swing, shell=True,timeout=3600,bufsize=655360)
        #subprocess.Popen(exec_swing, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=655360, encoding="utf-8")
        command1 = """cat /tmp/result_user_count|grep "\[user_count/user_count\]"|awk '{if($3>0) print $0}' > /tmp/result_user_count.txt""".replace('user_count',str(i))
        subprocess.run(command1, shell=True)
        #数据入库
        sql_text = '/tmp/result_'+str(i)+'.txt'
        #sql_load = """LOAD DATA INFILE "{0}" INTO TABLE otpstest.t_tmp(@1,`DBINFO`,`TPS_TIME`,`USERS`, `TPM`,`TPS`,`USER_CPU`,`SYSTEM_CPU`, `WAIT_CPU`,`IDLE_CPU`,`BI_IO`,`BO_IO`)""".format(sql_text)
        sql_into_detail = """insert into otpstest.t_history_detail (DBINFO,IPINFO,TPS_TIME,USERS, TPM,TPS,USER_CPU,SYSTEM_CPU, WAIT_CPU,IDLE_CPU,BI_IO,BO_IO) select `DBINFO`,`IPINFO`,`TPS_TIME`,`USERS`, `TPM`,`TPS`,`USER_CPU`,`SYSTEM_CPU`, `WAIT_CPU`,`IDLE_CPU`,`BI_IO`,`BO_IO` from otpstest.`t_tmp`"""
        sql_into_history = """insert into otpstest.t_history (DBINFO,IPINFO,BEGIN_TIME,END_TIME,USERS,MAX_TPS,MIN_TPS,AVG_TPS,USER_CPU,SYSTEM_CPU, WAIT_CPU,IDLE_CPU,BI_IO,BO_IO) values ('{0}','{1}',str_to_date('{2}','%Y-%m-%d %T'),str_to_date('{3}','%Y-%m-%d %T'),{4},{5},{6},{7},{8},{9},{10},{11},{12},{13})"""
        sql_compute_tps = """select BEGIN_TIME,END_TIME,MAX_TPS,MIN_TPS,AVG_TPS,t2.USER_CPU,SYSTEM_CPU,WAIT_CPU,IDLE_CPU,BI_IO,BO_IO 
                               from (select min(TPS_TIME) BEGIN_TIME,max(TPS_TIME) END_TIME,max(TPS) MAX_TPS,min(TPS) MIN_TPS,convert(avg(TPS),SIGNED) AVG_TPS from t_tmp where TPS > 0) t1
                               join t_tmp t2 on t1.max_tps = t2.tps 
                               limit 1"""
        sql_into_tmp = """insert into otpstest.t_tmp (DBINFO,IPINFO,TPS_TIME,USERS, TPM,TPS,USER_CPU,SYSTEM_CPU, WAIT_CPU,IDLE_CPU,BI_IO,BO_IO) values ('{db_info}','{ip_info}',str_to_date('{d_time}','%Y-%m-%d %T'),'{USERS}',{TPM},{TPS},{USER_CPU},{SYSTEM_CPU},{WAIT_CPU},{IDLE_CPU},{BI_IO},{BO_IO})"""
        sql_trunc_tmp = """truncate table otpstest.t_tmp"""
        list_result = f_getlist(sql_text)
        if list_result:
            now_date = datetime.now().strftime("%Y-%m-%d")+' '
            for i1 in list_result:
                if i1[4] == '0' and i1[5] == '0' and i1[6] == '0' and i1[7] == '0' and i1[8] == '0' and i1[9] == '0':
                    print('没有获取到OS cpu使用率信息，请检查操作系统连接信息后重试...')
                    sys.exit()
                else:
                    sql_exec = sql_into_tmp.format(db_info = settings.db_info,ip_info = settings.ora_ip,d_time=now_date+i1[0],USERS=i1[1],TPM=i1[2],TPS=i1[3],USER_CPU=i1[4],SYSTEM_CPU=i1[5],WAIT_CPU=i1[6],IDLE_CPU=i1[7],BI_IO=i1[8],BO_IO=i1[9])
                    m_conn.execsql(sql_exec)
            m_conn.execsql(sql_into_detail)
            res_compute_tps = m_conn.execsql(sql_compute_tps)
            #print(res_compute_tps)
            list_tmp = [settings.db_info,settings.ora_ip,res_compute_tps[0][0].strftime("%Y-%m-%d %H:%M:%S"),res_compute_tps[0][1].strftime("%Y-%m-%d %H:%M:%S"),i,res_compute_tps[0][2],res_compute_tps[0][3],res_compute_tps[0][4],res_compute_tps[0][5],res_compute_tps[0][6],res_compute_tps[0][7],res_compute_tps[0][8],res_compute_tps[0][9],res_compute_tps[0][10]]
            #print(list_tmp)
            list_dic_final.insert(-1,list(list_tmp))
            exec_sql = sql_into_history.format(list_tmp[0],list_tmp[1],list_tmp[2],list_tmp[3],list_tmp[4],list_tmp[5],list_tmp[6],list_tmp[7],list_tmp[8],list_tmp[9],list_tmp[10],list_tmp[11],list_tmp[12],list_tmp[13])
            #print(exec_sql)
            m_conn.execsql(exec_sql)
            m_conn.execsql(sql_trunc_tmp)
            time.sleep(10)
        else:
            print('文件读取失败')

    list_tittle = ['数据库名','IP地址','开始时间','结束时间','连接用户数','最大TPS','最小TPS','平均TPS','USER_CPU(maxtps)','SYSTEM_CPU(maxtps)','WAIT_CPU(maxtps)','IDLE_CPU(maxtps)','BI_IO(maxtps)','BO_IO(maxtps)']
    list_dic_final.insert(0,list_tittle)
    #print(list_dic_final)
    #结果集输出到屏幕
    try:
        print("=====" + settings.db_info + "=====")
        row = PrettyTable()
        num = 0
        for item in list_dic_final:  # item是一个列表
            if num == 0:
                row.field_names = item
                num = num + 1
            else:
                row.add_row(item)
        print(row)  # 输出
    except:
        print(settings.db_info + ": show error")
    else:
        pass

if __name__ == '__main__':

    #ImportData()
    #OltpTest()
    parser = argparse.ArgumentParser(description='Oracle Swingbench Tps Test Tool')
    parser.add_argument('-run',help="输入importdata开始导入soe的数据&&输入tpstest开始压测",type=str)
    results=parser.parse_args()
    if results.run == 'importdata':
        ImportData()
    if results.run == 'tpstest':
        OltpTest()



