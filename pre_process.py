#!/usr/bin/python
# -*- coding: UTF-8 -*-
# Author: pgy20@mails.tsinghua.edu.cn
# Date: 2020-10-24
# Function: pre-process the wifi data_rssi_rough&data_rssi_1 from wifi sniffer

import mysql.connector
import os


# 连接MySQL数据库
def connect_mysql():
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="123456",
        database="wifidetection"
    )
    return mydb


# 为收集到的wifi探测记录查询厂商信息
def find_manufacturer(mydb, mac):
    mycursor = mydb.cursor()
    manufacturer_info = mac[0:8].replace(':', '-')
    sql = 'select manufacturer from mac where mac=%s'
    val = (manufacturer_info,)
    mycursor.execute(sql, val)
    manufacturer = mycursor.fetchone()
    mycursor.close()
    return 'unknown' if manufacturer is None else manufacturer[0]


# 将某文件中记录的wifi探测记录处理后存入数据库
def insert_detection_from_file(mydb, table, filename):
    ref_distance = ''
    if table == 'rssi_analysis_rough':
        ref_distance = int(filename[filename.rfind('_')+1:filename.rfind('.')])
    elif table == 'rssi_analysis_detail':
        ref_distance = float(filename[-7:-4].replace('_', '.'))
    cursor = mydb.cursor()
    with open(filename, 'r', encoding='utf-8') as f:
        detections = f.readlines()
    processed_detections = []
    for line in detections:
        line = line[:-1].split('|')[1:]
        # print(line)
        line[-2] = find_manufacturer(mydb, line[0])
        for i in range(2, 9):
            if i != 3:
                line[i] = int(line[i])
            else:
                line[i] = int(line[i], base=16)
        # line[8] = int(line[8])
        if table.startswith('rssi_analysis'):
            line.append(ref_distance)
        print(line)
        line = tuple(line)
        processed_detections.append(line)
    print(processed_detections)

    sql = 'insert into ' + table + ' ' \
          '(source,destination,maintype,subtype,channel,rssi,' \
          'powersaving,isrouter,remain,detectedtime,manufacturer,detectedday)' \
          'values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);'
    if table.startswith('rssi_analysis'):
        sql = 'insert into ' + table + ' ' \
                                        '(source,destination,maintype,subtype,channel,rssi,' \
                                        'powersaving,isrouter,remain,detectedtime,manufacturer,detectedday,refdistance)' \
                                        'values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);'
    try:
        cursor.executemany(sql, processed_detections)
        mydb.commit()
    except Exception:
        print('Error: Exception happened during database operations!')
        mydb.rollback()
    cursor.close()


def get_all_file(path):
    files = os.listdir(path)
    s = []
    for file in files:
        if not os.path.isdir(file):
            s.append(path+'/'+file)
    return s


def insert_detection_data(mydb, table, filepath):
    filenames = get_all_file(filepath)
    print(filenames)
    for filename in filenames:
        insert_detection_from_file(mydb, table, filename)


if __name__ == "__main__":
    mydb = connect_mysql()
    # 打开data_rssi_0等文件夹并将数据导入mysql
    # insert_detection_data(mydb, "rssi_analysis_detail", "data_rssi_detail")
    insert_detection_data(mydb, "detection", "wifi_detection_1")
    mydb.close()
