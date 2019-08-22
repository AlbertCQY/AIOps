#!/usr/bin/env python
# -*- coding: utf-8 -*-
# !/usr/bin/python
import paramiko
import os, sys, time
from paramiko_expect import SSHClientInteraction
from functools import wraps
from datetime import datetime


def timethis(func):
    """
    时间装饰器，计算函数执行所消耗的时间
    :param func:
    :return:
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = datetime.now()
        result = func(*args, **kwargs)
        end = datetime.now()
        print(func.__name__, end - start)
        return result
    return wrapper

class SSHManager:
    def __init__(self, host, usr, passwd):
        self._host = host
        self._usr = usr
        self._passwd = passwd
        self._ssh = None
        self._sftp = None
        self._sftp_connect()
        self._ssh_connect()

    def delsession(self):
        if self._ssh:
            self._ssh.close()
        if self._sftp:
            self._sftp.close()

    def _sftp_connect(self):
        try:
            transport = paramiko.Transport((self._host, 22))
            transport.connect(username=self._usr, password=self._passwd)
            self._sftp = paramiko.SFTPClient.from_transport(transport)
        except Exception as e:
            raise RuntimeError("sftp connect failed [%s]" % str(e))

    def _ssh_connect(self):
        try:
            # 创建ssh对象
            self._ssh = paramiko.SSHClient()
            # 允许连接不在know_hosts文件中的主机
            self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            # 连接服务器
            self._ssh.connect(hostname=self._host,
                              port=22,
                              username=self._usr,
                              password=self._passwd,
                              timeout=5)
            self.channel = self._ssh.invoke_shell()
            self.channel.settimeout(100)
        except Exception:
            raise RuntimeError("ssh connected to [host:%s, usr:%s, passwd:%s] failed" %
                               (self._host, self._usr, self._passwd))
    def get_channel(self):
        return self._ssh.invoke_shell()
    @timethis
    def _upload_file(self, local_file, remote_file):
        """
        通过sftp上传本地文件到远程
        :param local_file:
        :param remote_file:
        :return:
        """
        try:
            self._sftp.put(local_file, remote_file)
        except Exception as e:
            raise RuntimeError('upload failed [%s]' % str(e))
    @timethis
    def _download_file(self, remote_file,local_file):
        """
        通过sftp下载远程文件到本地
        :param remote_file:
        :param local_file:
        :return:
        """
        try:
            self._sftp.get( remote_file,local_file)
        except Exception as e:
            raise RuntimeError('download failed [%s]' % str(e))
    def _exec_command(self, cmd, path='~'):
        """
        通过ssh执行远程命令,命令不需要交互
        :param cmd:
        :return:
        """
        try:
            stdin, stdout, stderr = self._ssh.exec_command('cd ' + path + ';' + cmd)
            return stdout.read().decode()
        except Exception as e:
            raise RuntimeError('Exec command [%s] failed' % str(cmd))

    def ssh_exec_cmd(self, cmd, path='~'):
        """
        通过ssh连接到远程服务器，执行给定的命令,命令不需要交互,获取单次执行命令的结果
        :param cmd: 执行的命令
        :param path: 命令执行的目录
        :return: 返回结果
        """
        try:
            result = self._exec_command('cd ' + path + ';' + cmd)
            return  result
        except Exception:
            raise RuntimeError('exec cmd [%s] failed' % cmd)
    def ssh_exec_cmd2(self, cmd, path='~'):
        """
        通过ssh连接到远程服务器，执行给定的命令,需要交互
        :param cmd: 执行的命令
        :param path: 命令执行的目录
        :return: 返回结果
        """
        if '''~/.ssh/authorized_keys''' in cmd:
            # buff = ''
            resp = ''
            channel = self.get_channel()
            channel.send('cd ' + path + ';' + cmd + '\n')
            while not resp.endswith('password: '):
                try:
                    resp = channel.recv(9999).decode('utf8')
                    channel.send('hostname\n')
                    ch_res = channel.recv(9999).decode('utf8')
                except Exception as e:
                    print('Error info:%s connection authorized_keys.' % (str(e)))
                    channel.close()
                    self._ssh.close()
                    sys.exit()
                # buff += resp
                if not resp.find('(yes/no)') == -1:
                    channel.send('yes\n')
            channel.send(init_p.init_password + '\n')
    def setupselfssh(self,password, cmd, path='~'):
        """
        通过ssh连接到远程服务器，执行给定的命令,命令不需要交互,获取单次执行命令的结果
        :param cmd: 执行的命令
        :param path: 命令执行的目录
        :return: 返回结果
        """
        # try:
        #     result = self._exec_command('cd ' + path + ';' + cmd)
        #     print(result)
        # except Exception:
        #     raise RuntimeError('exec cmd [%s] failed' % cmd)
        PROMPT1 ="Are you sure.*"
        PROMPT2 = ".*password: "
        PROMPT3 = "Do you want to continue.*"
        PROMPTZ = ".*~\][#\$] "

        with SSHClientInteraction(self._ssh, timeout=10, encoding='utf-8', display=False, buffer_size=100000) as interact:
            if cmd.endswith("-advanced -noPromptPassphrase"):

                interact.send('cd ' + path + ';' + cmd)
                i = -1
                while (i!=5):
                    i = interact.expect([PROMPT1,PROMPT2,PROMPT3,PROMPTZ],timeout=10)
                    if i == 0 or i == 2:
                        interact.send('yes')
                    elif i == 1:
                        interact.send(password)
                    elif i == 3:
                        cmd_output_uname = interact.current_output_clean
                        interact.send('exit')
                        interact.expect()
                        return [5,interact]
            elif cmd.endswith("""cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys"""):
                interact.send('cd ' + path + ';' + cmd)
                #time.sleep(1)
                interact.expect(PROMPT1)
                interact.send('yes')
                #time.sleep(1)
                interact.expect(PROMPT2)
                #time.sleep(1)
                interact.send(password)
                interact.expect(PROMPTZ)
                cmd_output_uname = interact.current_output_clean
                interact.send('exit')
            elif cmd.startswith("""scp ~/.ssh/authorized_keys"""):
                interact.send('cd ' + path + ';' + cmd)
                #time.sleep(1)
                interact.expect(PROMPT2)
                interact.send(password)
                interact.expect(PROMPTZ)
                cmd_output_uname = interact.current_output_clean
                interact.send('exit')
            elif not cmd.find("date;ssh") == -1:
                try:
                    interact.send('cd ' + path + ';' + cmd)
                    #time.sleep(1)
                    interact.expect(PROMPT1)
                    interact.send('yes')
                    #time.sleep(1)
                    interact.expect(PROMPT1)
                    interact.send('yes')
                    interact.expect(PROMPTZ)
                    cmd_output_uname = interact.current_output_clean
                    interact.send('exit')
                except Exception as e:
                    pass
#安装部署服务器和目标主机之间建立了ssh 信任的情况下，不需要知道目标主机的密码，就可以建立ssh连接
#默认使用oracle用户的private key,端口默认为22
class SSHManager2:
    def __init__(self, host, usr):
        pkey_file = '/home/{0}/.ssh/id_rsa'.format(usr)
        pkey = paramiko.RSAKey.from_private_key_file(pkey_file)
        self._host = host
        self._usr = usr
        self._pkey = pkey
        self._ssh = None
        self._sftp = None
        self._ssh_connect()
        self._sftp_connect()

    def delsession(self):
        if self._ssh:
            self._ssh.close()
        if self._sftp:
            self._sftp.close()

    def _sftp_connect(self):
        try:
            transport = paramiko.SSHClient()
            transport.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            transport.connect(hostname= self._host,port = 22,username=self._usr, pkey=self._pkey)
            t_sftp = transport.get_transport()
            self._sftp = paramiko.SFTPClient.from_transport(t_sftp)
        except Exception as e:
            raise RuntimeError("sftp connect failed [%s]" % str(e))

    def _ssh_connect(self):
        try:
            # 创建ssh对象
            self._ssh = paramiko.SSHClient()
            # 允许连接不在know_hosts文件中的主机
            self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            # 连接服务器
            self._ssh.connect(hostname=self._host,
                              port=22,
                              username=self._usr,
                              pkey=self._pkey,
                              timeout=5)
            self.channel = self._ssh.invoke_shell()
            self.channel.settimeout(100)
        except Exception:
            raise RuntimeError("ssh connected to [host:%s, usr:%s, passwd:%s] failed" %
                               (self._host, self._usr, self._passwd))
    def get_channel(self):
        return self._ssh.invoke_shell()
    @timethis
    def _upload_file(self, local_file, remote_file):
        """
        通过sftp上传本地文件到远程
        :param local_file:
        :param remote_file:
        :return:
        """
        try:
            self._sftp.put(local_file, remote_file)
        except Exception as e:
            raise RuntimeError('upload failed [%s]' % str(e))
    @timethis
    def _download_file(self, remote_file,local_file):
        """
        通过sftp下载远程文件到本地
        :param remote_file:
        :param local_file:
        :return:
        """
        try:
            self._sftp.get( remote_file,local_file)
        except Exception as e:
            raise RuntimeError('download failed [%s]' % str(e))
    def _exec_command(self, cmd, path='~'):
        """
        通过ssh执行远程命令,命令不需要交互
        :param cmd:
        :return:
        """
        try:
            stdin, stdout, stderr = self._ssh.exec_command('cd ' + path + ';' + cmd)
            return stdout.read().decode()
        except Exception as e:
            raise RuntimeError('Exec command [%s] failed' % str(cmd))

    def ssh_exec_cmd(self, cmd, path='~'):
        """
        通过ssh连接到远程服务器，执行给定的命令,命令不需要交互,获取单次执行命令的结果
        :param cmd: 执行的命令
        :param path: 命令执行的目录
        :return: 返回结果
        """
        try:
            result = self._exec_command('cd ' + path + ';' + cmd)
            return  result
        except Exception:
            raise RuntimeError('exec cmd [%s] failed' % cmd)
    def ssh_exec_cmd2(self, cmd, path='~'):
        """
        通过ssh连接到远程服务器，执行给定的命令,需要交互
        :param cmd: 执行的命令
        :param path: 命令执行的目录
        :return: 返回结果
        """
        if '''~/.ssh/authorized_keys''' in cmd:
            # buff = ''
            resp = ''
            channel = self.get_channel()
            channel.send('cd ' + path + ';' + cmd + '\n')
            while not resp.endswith('password: '):
                try:
                    resp = channel.recv(9999).decode('utf8')
                    channel.send('hostname\n')
                    ch_res = channel.recv(9999).decode('utf8')
                except Exception as e:
                    print('Error info:%s connection authorized_keys.' % (str(e)))
                    channel.close()
                    self._ssh.close()
                    sys.exit()
                # buff += resp
                if not resp.find('(yes/no)') == -1:
                    channel.send('yes\n')
            channel.send(init_p.init_password + '\n')



if __name__ == '__main__':
    ssh = SSHManager('1.1.3.111','oracle','bigbangdata.cn')
    command1 = ssh.ssh_exec_cmd('hostname')
    print(command1)
    #ssh._upload_file('/root/cqy1','/home/oracle/cqy1')
    #c






