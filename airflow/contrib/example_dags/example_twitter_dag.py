# -*- coding: utf-8 -*-
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
# --------------------------------------------------------------------------------
# Written By: Ekhtiar Syed
# Last Update: 8th April 2016
# Caveat: This Dag will not run because of missing scripts.
# The purpose of this is to give you a sample of a real world example DAG!
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Load The Dependencies
# --------------------------------------------------------------------------------
"""
This is an example dag for managing twitter data.
"""
from datetime import date, timedelta

import airflow
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.hive_operator import HiveOperator
from airflow.operators.python_operator import PythonOperator

# --------------------------------------------------------------------------------
# Create a few placeholder scripts. In practice these would be different python
# script files, which are imported in this section with absolute or relative imports
# --------------------------------------------------------------------------------


def fetchtweets():
    """
    This is a placeholder for fetchtweets.
    """


def cleantweets():
    """
    This is a placeholder for cleantweets.
    """


def analyzetweets():
    """
    This is a placeholder for analyzetweets.
    """


def transfertodb():
    """
    This is a placeholder for transfertodb.
    """


# --------------------------------------------------------------------------------
# set default arguments
# --------------------------------------------------------------------------------

default_args = {
    'owner': 'Ekhtiar',
    'depends_on_past': False,
    'start_date': airflow.utils.dates.days_ago(5),
    'email': ['airflow@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    # 'queue': 'bash_queue',
    # 'pool': 'backfill',
    # 'priority_weight': 10,
    # 'end_date': datetime(2016, 1, 1),
}

with DAG(
    dag_id='example_twitter_dag',
    default_args=default_args,
    schedule_interval="@daily"
) as dag:

    # --------------------------------------------------------------------------------
    # This task should call Twitter API and retrieve tweets from yesterday from and to
    # for the four twitter users (Twitter_A,..,Twitter_D) There should be eight csv
    # output files generated by this task and naming convention
    # is direction(from or to)_twitterHandle_date.csv
    # --------------------------------------------------------------------------------

    fetch_tweets = PythonOperator(
        task_id='fetch_tweets',
        python_callable=fetchtweets
    )

    # --------------------------------------------------------------------------------
    # Clean the eight files. In this step you can get rid of or cherry pick columns
    # and different parts of the text
    # --------------------------------------------------------------------------------

    clean_tweets = PythonOperator(
        task_id='clean_tweets',
        python_callable=cleantweets
    )

    clean_tweets << fetch_tweets

    # --------------------------------------------------------------------------------
    # In this section you can use a script to analyze the twitter data. Could simply
    # be a sentiment analysis through algorithms like bag of words or something more
    # complicated. You can also take a look at Web Services to do such tasks
    # --------------------------------------------------------------------------------

    analyze_tweets = PythonOperator(
        task_id='analyze_tweets',
        python_callable=analyzetweets
    )

    analyze_tweets << clean_tweets

    # --------------------------------------------------------------------------------
    # Although this is the last task, we need to declare it before the next tasks as we
    # will use set_downstream This task will extract summary from Hive data and store
    # it to MySQL
    # --------------------------------------------------------------------------------

    hive_to_mysql = PythonOperator(
        task_id='hive_to_mysql',
        python_callable=transfertodb
    )

    # --------------------------------------------------------------------------------
    # The following tasks are generated using for loop. The first task puts the eight
    # csv files to HDFS. The second task loads these files from HDFS to respected Hive
    # tables. These two for loops could be combined into one loop. However, in most cases,
    # you will be running different analysis on your incoming incoming and outgoing tweets,
    # and hence they are kept separated in this example.
    # --------------------------------------------------------------------------------

    from_channels = ['fromTwitter_A', 'fromTwitter_B', 'fromTwitter_C', 'fromTwitter_D']
    to_channels = ['toTwitter_A', 'toTwitter_B', 'toTwitter_C', 'toTwitter_D']
    yesterday = date.today() - timedelta(days=1)
    dt = yesterday.strftime("%Y-%m-%d")
    # define where you want to store the tweets csv file in your local directory
    local_dir = "/tmp/"
    # define the location where you want to store in HDFS
    hdfs_dir = " /tmp/"

    for channel in to_channels:

        file_name = "to_" + channel + "_" + yesterday.strftime("%Y-%m-%d") + ".csv"

        load_to_hdfs = BashOperator(
            task_id="put_" + channel + "_to_hdfs",
            bash_command="HADOOP_USER_NAME=hdfs hadoop fs -put -f " +
                         local_dir + file_name +
                         hdfs_dir + channel + "/"
        )

        load_to_hdfs << analyze_tweets

        load_to_hive = HiveOperator(
            task_id="load_" + channel + "_to_hive",
            hql="LOAD DATA INPATH '" +
                hdfs_dir + channel + "/" + file_name + "' "
                "INTO TABLE " + channel + " "
                "PARTITION(dt='" + dt + "')"
        )
        load_to_hive << load_to_hdfs
        load_to_hive >> hive_to_mysql

    for channel in from_channels:
        file_name = "from_" + channel + "_" + yesterday.strftime("%Y-%m-%d") + ".csv"
        load_to_hdfs = BashOperator(
            task_id="put_" + channel + "_to_hdfs",
            bash_command="HADOOP_USER_NAME=hdfs hadoop fs -put -f " +
                         local_dir + file_name +
                         hdfs_dir + channel + "/"
        )

        load_to_hdfs << analyze_tweets

        load_to_hive = HiveOperator(
            task_id="load_" + channel + "_to_hive",
            hql="LOAD DATA INPATH '" +
                hdfs_dir + channel + "/" + file_name + "' "
                "INTO TABLE " + channel + " "
                "PARTITION(dt='" + dt + "')"
        )

        load_to_hive << load_to_hdfs
        load_to_hive >> hive_to_mysql