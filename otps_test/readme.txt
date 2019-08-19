0、清理环境
drop user soe cascade;
drop tablespace soe including contents and datafiles;
1、mysql 压测结果集表
create database otpstest DEFAULT CHARSET=utf8;
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
2、导出soe用户
expdp \'sys/bigbangdata.cn@1.1.3.111:1521/orcl12c as sysdba\' schemas=soe directory=soe_dir dumpfile=soe_%U.dmp logfile=soe_expdp.log parallel=6 compression=all
impdp \'sys/bigbangdata.cn@1.1.3.111:1521/orcl12c as sysdba\' schemas=soe directory=soe_dir dumpfile=soe_%U.dmp logfile=soe_expdp.log parallel=6 JOB_NAME=impdp_soe

3、压测
处理下结果
cat oltp_test.log|grep "\[200/200\]"|awk '{if($3>0) print $0}' > oltp_test2.log
入库
测试