from bs4 import BeautifulSoup
import requests
import html5lib
import os, csv
import datetime as dt
import re, json
import pandas as pd


class joinJob:

    def __init__(self, id):
        self.id = id

    def getJobId(self):
        return self.id

    def sumtime(self, value):
        """
        Converts time to seconds
        :param: value Time in #mins, #sec format
        :type String
        :return:
        :rtype: int in secs

        Example: 50mins, 20 secs -> 3020
        """
        time = value.split(',')
        sumtime = 0
        for t in time:
            mins = re.compile(".*mins$")
            m = mins.match(t)
            if m:
                sumtime += 60 * int(m.group(0).replace("mins", ""))
            secs = re.compile(".*sec$")
            m = secs.match(t)
            if m:
                sumtime += int(m.group(0).replace("sec", ""))
        return sumtime

    def fetchJobOverview(self):
        """
        Fetches job overview from Hadoop Application tracker
        :return: return All node statistics
        :rtype: json table object that can be evaluated as a list of lists
        """
        hadoop_cluster_url = 'http://ilhadoop1.stanford.edu:19888/jobhistory/'
        hadoop_namenode = 'job_1454535876543_'
        hadoop_job_overview_url = (hadoop_cluster_url + 'job/' +
                                   hadoop_namenode + self.id)
        print hadoop_job_overview_url
        job = {}
        job['id'] = self.id
        html = requests.get(hadoop_job_overview_url).text
        soup = BeautifulSoup(html, 'html5lib')
        table = soup.find('table', attrs={'class': 'info'})
        tbody = table.findChild('tbody')
        th = tbody.findChildren('th')
        for thi in th:
            thi.findNext('td')
            key = thi.text.strip().replace(":", "").replace("\n", "")
            if key:
                job[key] = thi.findNext('td').text.strip().replace(":", "").replace("\n", "")
        for k, v in job.iteritems():
            if (k == 'Average Shuffle Time' or
                    k == 'Elapsed' or
                    k == 'Average Merge Time' or
                    k == 'Average Map Time' or
                    k == 'Average Reduce Time'):
                job[k] = self.sumtime(v)
        return job

    def fetchHadoopWebStats(self, nodeType):
        '''
        Fetches data from Hadoop Application tracker
        :param nodeType: reducer or mapper
        :type nodeType: String: A choice between 'r' or 'm'
        :return: return All node statistics
        :rtype: json table object that can be evaluated as a list of lists
        '''
        pattern = re.compile('var tasksTableData=(.*)', re.DOTALL)
        hadoop_cluster_url = 'http://ilhadoop1.stanford.edu:19888/jobhistory/'
        # job_id = 'job_1454535876543_' + self.id
        hadoop_namenode = 'job_1454535876543_'
        # hadoop_job_overview_url = (hadoop_cluster_url + 'job/' +
        #                            hadoop_namenode + self.id)

        hadoop_job_tasks_url = (hadoop_cluster_url + 'tasks/' +
                                hadoop_namenode + self.id)

        # hadoop_reduce_stats = hadoop_job_tasks_url + '/r'
        # hadoop_map_stats = hadoop_job_tasks_url + '/m'

        if nodeType == 'reducer' or 'mapper':
            html = requests.get(hadoop_job_tasks_url + '/' + nodeType).text
            soup = BeautifulSoup(html, 'html5lib')
            scripts = soup.find_all("script")
            for script in scripts:
                if script:
                    script = script.string.lstrip()
                    m = pattern.search(script)
                    if m:
                        return json.loads(m.groups()[0])
        else:
            return None
