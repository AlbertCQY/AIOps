#!/usr/bin/env python
# -*- coding:utf-8 -*-

import cx_Oracle as db
import sys
import settings
import threading
#threading用来控制线程 这里用threading.Timer来控制cx_Oracle执行语句的自动超时
#http://stackoverflow.com/questions/2374079/set-database-connection-timeout-in-python

class Oracle_Conn():
    def __init__(self,username,password,ip,port,servicename):
        try:
            if username=='sys':
                self.con=db.connect("{0}/{1}@{2}:{3}/{4}".format(username, password, ip,port, servicename),mode=db.SYSDBA)
            else:
                self.con=db.connect("{0}/{1}@{2}:{3}/{4}".format(username, password, ip,port, servicename))
                
            self.cur=db.Cursor(self.con)
        except Exception as errmsg:
            print('connect error the error msg is:',str(errmsg))
            sys.exit()
        else:
            pass

    def execsql(self,sqltext,timeout=60):
        try:
            t=threading.Timer(timeout,self.cancel)#超时会执行函数cancel()
            t.start() #开始任务 开始计时
            self.cur.execute(sqltext)
            t.cancel() #正常结束任务
        except Exception as errmsg:
            #语句执行失败或者超时
            if str(errmsg).startswith("ORA-01013"):#ORA-01013: user requested cancel of current operation\n
                return "执行用时超过阀值"+str(timeout)+"秒,系统自动中断"
            else:
                return str(errmsg)
        else:
            #语句执行成功
            #(fetchone出来是一个元祖 返回第一行)  fetchall返回多行 是列表 列表的元素是元祖
            #dml和explain plan和存储过程都是返回None
            try:
                res=self.cur.fetchall()
            except:
                # 如果没有返回结果那么fetchall会报错
                return None
            else:
                return res
        finally:
            try:
                t.cancel()
            except:
                pass
            else:
                pass



    def close_commit(self):#提交后关闭连接
        self.con.commit()
        self.cur.close()
        self.con.close()

    def close_rollback(self):#回滚后关闭连接
        self.con.rollback()
        self.cur.close()
        self.con.close()

    def cancel(self):
        self.con.cancel()#取消正在执行的sql 不做提交和回滚动作



if __name__ == '__main__':
    try:
       connection=Oracle_Conn(settings.ora_usr,settings.ora_pass,settings.ora_ip,settings.ora_port,settings.ora_srvname)
    except Exception as err:
        print('+++++++++++++++++++++++++++++++++++++++++++++++')
        print("connect wrong",err)
    else:
        print('+++++++++++++++++++++++++++++++++++')
        print(connection.execsql("select * from v$instance"))
        print(connection.execsql("select sysdate from dual"))
        ###

