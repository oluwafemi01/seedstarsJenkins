import jenkins
import requests
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_database
from sqlalchemy.orm import sessionmaker
import datetime


Base = declarative_database()

def jenkins_connection(url, username, password):
    """ Function to connect the Jenkins API """
    server = jenkins.Jenkins(url, username=username, password=password)
    return server


def initializeDatabase():
    """ Function to initialize the SqLite """
    engine = create_engine('sqlite:///cli.db', echo=False)
    session = sessionmaker(bind=engine)()
    Base.metadata.create_all(engine)
    return session


def add_job(session, joblist):
    """ Function to Add a Job in the job list """
    for job in joblist:
        session.add(job)
    session.commit()


def getLastJobId(session, name):
	""" Function to get a previous job """
    job = session.query(Jobs).filter_by(name=name).order_by(Jobs.jen_id.desc()).first()
    if (job != None):
        return job.jen_id
    else:
        return None


class Jobs(Base):
    __tablename__ = 'Jobs'

    id = Column(Integer, primary_key = True)
    jen_id = Column(Integer)
    name = Column(String)
    timeStamp = Column(DateTime)
    result = Column(String)
    building = Column(String)
    estimatedDuration = Column(String)

def createJobList(start, lastBuildNumber, jobName):
    job_list = []
    for i in range(start + 1, lastBuildNumber + 1):
        current = server.get_build_info(jobName, i)
        current_job = Jobs()
        current_job.jen_id = current['id']
        current_job.building = current['building']
        current_job.estimatedDuration = current['estimatedDuration']
        current_job.name = jobName
        current_job.result = current['result']
        current_job.timeStamp = datetime.datetime.fromtimestamp(long(current['timestamp'])*0.001)
        job_list.append(current_job)
    return job_list


url = 'http://localhost:8000'
username = raw_input('Your username: ')
password = raw_input('Your Password: ')
server = jenkins_connection(url, username, password)

authenticated = False

try:
    server.get_whoami()
    authenticated = True
except jenkins.JenkinsException as ex:
    print 'There was an error in authentication!'
    authenticated = False


if authenticated:
    session = initializeDatabase()
    # get a list of all jobs
    jobs = server.get_all_jobs()
    for j in jobs:
        jobName = j['name'] # get job name
        lastJobId = getLastJobId(session, jobName) # get last locally stored job of this name
        lastBuildNumber = server.get_job_info(jobName)['lastBuild']['number']  # get last build number from Jenkins for this job 

        if lastJobId == None:
            start = 0
        else:
            start = lastJobId

        joblist = createJobList(start, lastBuildNumber, jobName)
        # add job to db
        add_job(session, joblist)