#!/usr/bin/python
# -*- coding: UTF-8 -*-
# Author: pgy20@mails.tsinghua.edu.cn
# Date: 2020-10-25
# Function: analyze the wifi data from wifi sniffer

# 1. For rssi day1:
# 0 meter: 2020-10-31 07:10:36 - 2020-10-31 07:12:06
# 1 meter: 2020-10-31 07:12:51 - 2020-10-31 07:15:19
# 5 meter: 2020-10-31 07:16:16 - 2020-10-31 07:21:18
# 10 meter: 2020-10-31 07:22:25 - 2020-10-31 07:24:44
# object mac address: B4:86:55:23:A3:95(My cellphone from HUAWEI)

# 2.For rssi day2:
# 0 meter: 2020-11-01 07:39:20 - 2020-11-01 07:42:45
# 1 meter: 2020-11-01 07:43:17 - 2020-11-01 07:46:06
# 5 meter: 2020-11-01 07:46:53 - 2020-11-01 07:49:16
# 10 meter: 2020-11-01 07:50:10 - 2020-11-01 07:54:05
# object mac address: B4:86:55:23:A3:95(My cellphone from HUAWEI)

# 3.For rssi detail analysis
# object mac address: B4:86:55:23:A3:95(My cellphone from HUAWEI)

# 4.For wifi detection day1-4

import mysql.connector
import datetime
import numpy as np
import plotly.offline as py
import plotly.graph_objs as go
import plotly.io as pio
import plotly.express as px
import math
import random
import pandas as pd


# 连接MySQL数据库
def connect_mysql():
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="123456",
        database="wifidetection"
    )
    return mydb


# 字符串转换成datetime日期
def str_to_datetime(str):
    return datetime.datetime.strptime(str, '%Y-%m-%d %H:%M:%S')


# 取目标设备某一时间段内的探测数据
def extract_detection_within_period(mydb, table, mac):
    cursor = mydb.cursor()
    sql = "select rssi,detectedtime,refdistance from " + table + " " \
          "where maintype = 0 and subtype = 4 and source = '" + mac + "';"
    cursor.execute(sql)
    distance_detection_sets = {}
    keys = []
    if table == 'rssi_analysis_rough':
        keys = [0, 1, 5, 10]
    else:
        keys = [round(i*0.6, 1) for i in range(0, 16)]
    print(keys)
    for i in keys:
        distance_detection_sets[i] = list()
    for x in cursor:
        distance_detection_sets[x[-1]].append(x[0])
    cursor.close()
    return distance_detection_sets


# 提取某时间窗口内unique的mac数
def device_counting_within_period(mydb, table, start_date, end_date):
    cursor = mydb.cursor()
    sql = 'select source,rssi,detectedtime,manufacturer from ' + table + ' ' \
          'where maintype = 0 and subtype = 4 and detectedtime>= %s and detectedtime < %s and isrouter=0'
    val = (start_date, end_date)
    cursor.execute(sql, val)
    mac_set = set()
    for x in cursor:
        mac_set.add(x[0])
    cursor.close()
    return mac_set


# 针对某天的数据画某时段探测到的mac-时间图像(time_window的单位是秒）
def draw_device_num_verse_time(mydb, table, date, start_time, duration_hour, time_window_second):
    date_zero = str_to_datetime(date + ' ' + start_time)
    date_tomorrow_zero = date_zero + datetime.timedelta(hours=duration_hour)  # 当前日期8点向后14小时，即22时
    time_x = []
    mac_number_y = []
    date_period_now = date_zero
    while date_period_now < date_tomorrow_zero:
        date_period_end = date_period_now + datetime.timedelta(seconds=time_window_second)
        time_x.append(date_period_now)
        mac_number_y.append(len(device_counting_within_period(mydb, table, date_period_now, date_period_end)))
        date_period_now = date_period_end
    layout = {
        'title': 'Mac detected in time windows',
        'xaxis': {'title': 'Time'},
        'yaxis': {'title': 'Unique Mac numbers'},
        # 'showlegend': False  # 不显示图例
    }
    # 画图（各time_window内的mac数）
    trace = go.Scatter(
        x=time_x,
        y=mac_number_y,
        mode='lines',
        name='lines'
    )
    data = [trace]
    fig = go.Figure(data, layout=layout)
    py.plot(fig, filename='plot/mac_time_' + date + '_' + str(time_window_second) + '.html')


# rssi分布计算
def rssi_distribution_analysis(mydb):
    # 2. 按所在日期（单位为天）分组
    # 3. 按time_window统计
    # 4. 将四个图画在一起，不连着的两天中间的时间给省略（试一下是不是可以）
    all_detections = get_all_detections(mydb, "detection")
    # 预计后面还有求rssi的分布这样的，还有热度图（先分析一下rssi的分布情况再说）
    all_rssi = [i for i in range(-100, 1)]
    rssi_dict = {}
    for i in all_rssi:
        rssi_dict[i] = 0
    for detection in all_detections:
        rssi_dict[detection[1]] += 1
    traces = []
    trace_bar = go.Bar(
        x=all_rssi,
        y=[rssi_dict[all_rssi[i]] for i in range(-100, 1)],
        name='identical rssi detected number bar',
        yaxis='y1'
    )
    traces.append(trace_bar)
    # rssi = a-10blg(distance) -> a=-57.77,b=2.197(R-square=0.9431)
    trace_rssi_distance = go.Scatter(
        x=all_rssi,
        y=[math.exp(((-57.77) - (all_rssi[i])) / (10 * 2.197)) for i in range(-100, 0)],
        name='expected distance respect to certain rssi',
        yaxis='y2',
        line={
            'width': 3
        }
    )
    traces.append(trace_rssi_distance)
    trace_line = go.Scatter(
        x=all_rssi,
        y=[rssi_dict[all_rssi[i]] for i in range(-100, 1)],
        name='identical rssi detected number line',
        yaxis='y1',
        line={
            'width': 3
        }
    )
    traces.append(trace_line)
    # Gaussian分布拟合结果(Rssi的分布）
    trace_rssi_gauss = go.Scatter(
        x=all_rssi,
        y=[6917*math.exp(-math.pow((float((all_rssi[i])-(-85.59))/8.953), 2)) +
           2592*math.exp(-math.pow((float((all_rssi[i])-(-75.41))/12.5), 2)) for i in range(-100, 0)],
        name='identical rssi detected number line (Gaussian fit)',
        yaxis='y1',
        line={
            'width': 3
        }
    )
    traces.append(trace_rssi_gauss)
    layout = {
        'title': 'RSSI Distribution & Distance-rssi',
        'xaxis': {'title': 'RSSI Measurement(dBm)', 'range': [-100, 0]},
        'yaxis': {'title': 'Total detected time'},
        'yaxis2': {'title': 'Distance respect to rssi', 'overlaying': 'y', 'side': "right"},
        'legend': {'font': {'size': 16}, 'x': 0.5, 'y': 0.8}
    }
    fig = go.Figure(data=traces, layout=layout)
    py.plot(fig, filename='plot/rssi_distribution_all_detections.html')


# 1. 找出所有的wifi探测记录
def get_all_detections(mydb, table):
    all_detections = []
    cursor = mydb.cursor()
    sql = 'select source,rssi,detectedtime,manufacturer,detectedday from ' + table \
          + ' where maintype = 0 and subtype = 4 and isrouter = 0'
    cursor.execute(sql)
    for line in cursor:
        all_detections.append(line)
    cursor.close()
    return all_detections


# 四天内的每个时刻分布
def draw_whole_four_day_detection(mydb, time_window_minute):
    all_detections = get_all_detections(mydb, "detection")
    # print(len(all_detections))
    # 1. 按天生成时间点（统计到8:00-22:00）
    detection_per_day = {}
    detect_day_start = ['2020-10-24 08:00:00', '2020-10-25 08:00:00', '2020-10-31 08:00:00', '2020-11-01 08:00:00']
    detect_time = [str_to_datetime(detect_day_start[j])+datetime.timedelta(minutes=time_window_minute*i)
                   for j in range(0, 4) for i in range(0, ((22-8)*60)//time_window_minute)]
    # print(detect_time)
    for i in range(len(detect_time)):
        detection_per_day[detect_time[i]] = set()

    for detection in all_detections:
        if detection[2].hour < 22:
            detection_window = str_to_datetime('' + str(detection[2].year) + '-' + str(detection[2].month) + '-'
                                               + str(detection[2].day) + ' ' + str(detection[2].hour)
                                               + ':' + str((detection[2].minute//time_window_minute)*time_window_minute)
                                               + ':00')
            detection_per_day[detection_window].add(detection[0])
    print(detection_per_day)
    # print(count)
    # 2. 按时间间隔统计数据
    trace = go.Scatter(
        x=[i for i in range(len(detect_time))],
        y=[len(detection_per_day[time]) for time in detect_time],
        name='MACs detected during all time windows',
        line={
            'width': 2
        }
    )
    layout = {
        'title': 'MACs detected during four-day expriment',
        'xaxis': {'title': 'time windows',
                  'tickmode': "array",
                  'tickvals': [i*time_window_minute for i in range(len(detect_time)//time_window_minute)],
                  'ticktext': [detect_time[i*time_window_minute].strftime("%m-%d %H:%M")
                               for i in range(len(detect_time)//time_window_minute)],
                  'tickangle': 45
                  },
        'yaxis': {'title': 'MACs'},
        'legend': {'font': {'size': 12}},
    }
    # 3. 画图
    data = [trace]
    fig = go.Figure(data=data, layout=layout)
    py.plot(fig, filename='plot/four_day_detection_mac_time.html')


# rssi-distance关系分析（两次测距在相同环境下进行）
def rssi_distance_analysis(mydb, table, object_mac):
    rssi_distance_sets = extract_detection_within_period(mydb, table, object_mac)
    print(rssi_distance_sets)
    keys = rssi_distance_sets.keys()
    layout = {
        'title': 'RSSI-Distance Measurement Scatter',
        'xaxis': {'title': 'RSSI Measurement(dBm)', 'range': [-100, 0]},
        'yaxis': {'title': 'Assumed Distance(m)', 'range': [-1, 12]},
        'showlegend': False  # 不显示图例
    }
    # 1.画出每个参考距离下的散点图
    traces1 = []
    for i in keys:
        trace = go.Scatter(
            x=rssi_distance_sets[i],
            y=[i] * len(rssi_distance_sets[i]),
            mode='markers'
        )
        traces1.append(trace)
    fig1 = go.Figure(data=traces1, layout=layout)
    py.plot(fig1, filename='plot/'+table+'_extreme_plot.html')
    # 2.去掉每个结果中的最大值和最小值之后再画散点图
    traces2 = []
    for i in keys:
        rssi_distance_sets[i].remove(max(rssi_distance_sets[i]))
        rssi_distance_sets[i].remove(min(rssi_distance_sets[i]))
        trace = go.Scatter(
            x=rssi_distance_sets[i],
            y=[i] * len(rssi_distance_sets[i]),
            mode='markers'
        )
        traces2.append(trace)
    fig2 = go.Figure(data=traces2, layout=layout)
    py.plot(fig2, filename='plot/'+table+'_medium_plot.html')
    # 3.去掉最大最小值之后取平均，计算rssi与距离的关系
    layout2 = {
        'title': 'Distance-RSSI Line and Fit Line',
        'yaxis': {'title': 'RSSI Value(dBm)', 'range': [-80, -20]},
        'xaxis': {'title': 'Assumed Distance(m)', 'range': [0, 9.5]},
        'legend': {'font': {'size': 16}, 'x': 0.8, 'y': 0.8}
    }
    avg_trace = go.Scatter(
        x=[i for i in keys],
        y=[np.mean(rssi_distance_sets[i]) for i in keys],
        name='Average rssi'
    )
    line_trace = []
    if table.rfind('detail')!=-1:
        fit_trace = go.Scatter(
            x=[(float(i)/100)*9.1 for i in range(0, 100)],
            y=[-57.77-2.197*10*math.log10((float(i)/100+0.01)*9.1) for i in range(0, 100)],
            name='Calculate rssi'
        )
        line_trace.append(fit_trace)
    line_trace.append(avg_trace)
    fig3 = go.Figure(data=line_trace, layout=layout2)
    py.plot(fig3, filename='plot/'+table+'_avg_plot.html')
    # rssi = a-10blg(distance) -> a=-57.77,b=2.197(R-square=0.9431)


# 分析设备厂商占比
def manufacturer_analysis(mydb):
    cursor = mydb.cursor()
    sql = 'select id,source,manufacturer from detection where maintype=0 and subtype=4 and isrouter=0'
    cursor.execute(sql)
    manufacturers = {}
    for x in cursor:
        if manufacturers.get(x[2]) is None:
            manufacturers[x[2]] = set()
        manufacturers[x[2]].add(x[1])
    print(manufacturers)
    print(len(manufacturers))
    total_num = sum([len(manufacturers[i]) for i in manufacturers.keys() if len(manufacturers[i]) > 1])
    result_data = []
    for (x, y) in sorted(manufacturers.items(), key=lambda kv: (len(kv[1]), kv[0])):
        print(x, len(y), str((float(len(y))/total_num)*100)+'%')
        if len(y) >= 2:
            result_data.append((x, len(y), (float(len(y))/total_num)*100))
    print(result_data)
    # 画饼图
    labels = [result_data[i][0] for i in range(0, len(result_data))]
    values = [result_data[i][2] for i in range(0, len(result_data))]
    print(labels)
    print(values)
    pyplt = py.offline.plot
    trace = [go.Pie(
        labels=labels,
        values=values,
        hoverinfo="label + percent")]
    layout = go.Layout(
        title='Manufacturer Distribution Pie Chart'
    )
    fig = go.Figure(data=trace, layout=layout)
    pyplt(fig, filename='plot/manufacturer_proportion.html')
    cursor.close()


# 计算某一时间段距离探测点圆心的设备分布情况
def mac_distance_distribution_during_period(mydb, start, end, time_window_minute):
    all_detections = get_all_detections(mydb, "detection")
    start_time = start
    end_time = start_time + datetime.timedelta(minutes=time_window_minute)
    while end_time <= end:
        detections_within_period = []
        for detection in all_detections:
            if detection[2] >= start_time and detection[2] < end_time:
                detections_within_period.append(detection)
        # 1.找设备
        devices = {}
        for detection in detections_within_period:
            if devices.get(detection[0]) is None:
                devices[detection[0]] = []
                devices[detection[0]].append(detection[1])
            else:
                devices[detection[0]].append(detection[1])
        scatter_points = []
        distances = []
        for key in devices.keys():
            devices[key] = calculate_distance_with_rssi(np.mean(devices[key]))  # 计算设备到探测点的平均距离
            x = random.uniform(-devices[key], devices[key])
            y = math.sqrt(math.pow(devices[key], 2)-pow(x, 2))*random.choice([-1, 1])
            scatter_points.append((x, y))
            distances.append(devices[key])
        trace = go.Scatter(
            x=[point[0] for point in scatter_points],
            y=[point[1] for point in scatter_points],
            mode='markers',
            name='Detection Random Point'
        )
        trace_origin = go.Scatter(
            x=[0],
            y=[0],
            mode="markers",
            name='Detection Base Point'
        )
        # print(len(scatter_points))
        layout = go.Layout(
            title='Possible Device Distribution from ' + start_time.strftime('%Y-%m-%d %H:%M:%S')
                  + 'to ' + end_time.strftime('%Y-%m-%d %H:%M:%S')
        )
        print(start_time, len(scatter_points), np.mean(distances), )

        fig = go.Figure(data=[trace, trace_origin], layout=layout)
        # py.plot(fig, filename="scatter/Possible Device Distribution from-" + start_time.strftime('%Y-%m-%d %H-%M-%S')
        #                       + '-to-' + end_time.strftime('%Y-%m-%d %H-%M-%S') + ".html")
        start_time = end_time
        end_time = end_time + datetime.timedelta(minutes=time_window_minute)


def calculate_distance_with_rssi(rssi):
    res = round(math.exp(((-57.77) - (rssi)) / (10 * 2.197)), 4)
    return res


if __name__ == "__main__":
    # main program
    mydb = connect_mysql()
    my_phone_mac = 'B4:86:55:23:A3:95'
    # rssi_distance_analysis(mydb, 'rssi_analysis_detail', my_phone_mac)
    # manufacturer_analysis(mydb)
    # draw_whole_four_day_detection(mydb, 10)

    start = str_to_datetime('2020-10-31 08:00:00')
    end = str_to_datetime('2020-10-31 22:00:00')
    # draw_device_num_verse_time(mydb, 'detection', '2020-10-31', '08:00:00', 14, 300)
    mac_distance_distribution_during_period(mydb, start, end, 20)
    # rssi_distribution_analysis(mydb)
    mydb.close()
