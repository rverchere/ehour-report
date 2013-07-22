#!/usr/bin/env python
# -*- coding:utf-8 -*-

import psycopg2
import smtplib
import sys
import time
import unicodedata
from ConfigParser import ConfigParser
from email.MIMEText import MIMEText
from optparse import OptionParser

VERSION = "0.1"

def sendTextMail(server, sender, rcpt, weeknum, text):
    fr = sender
    to = rcpt
    mail = MIMEText(text,'plain','utf-8')
    mail['From'] = fr
    mail['Subject'] = '[%s] Weekly Report' % weeknum
    mail['To'] = to
    smtp = smtplib.SMTP()
    smtp.connect(server)
    smtp.sendmail(fr, [to], mail.as_string())
    smtp.close()

def connectSql(host, dbname, user, password):
    conn_string = "host='%s' dbname='%s' user='%s' password='%s'" % \
                  (host, dbname, user, password)
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()
    return cursor

def reqSql(cursor, days):
    request = 'SELECT USR.LAST_NAME AS "userLastName",\
                   USR.FIRST_NAME AS "userFirstName",\
                   CUST.NAME AS "customerName",\
                   PRJ.NAME AS "projectName",\
                   ENTRY_DATE AS "dayDate",\
                   SUM(ENTRY.HOURS) AS "totalHours",\
                   ENTRY.COMMENT AS "comment"\
               FROM TIMESHEET_ENTRY ENTRY,\
                   CUSTOMER CUST,\
                   PROJECT PRJ,\
                   PROJECT_ASSIGNMENT PAG,\
                   USERS USR\
               WHERE ENTRY.ASSIGNMENT_ID = PAG.ASSIGNMENT_ID\
                   AND PAG.PROJECT_ID = PRJ.PROJECT_ID\
                   AND PRJ.CUSTOMER_ID = CUST.CUSTOMER_ID\
                   AND PAG.USER_ID = USR.USER_ID\
                   AND (ENTRY.ENTRY_DATE >= (now()::date - %s)\
                       AND ENTRY.ENTRY_DATE <= now()::date)\
               GROUP BY USR.LAST_NAME,\
                   USR.FIRST_NAME,\
                   CUST.NAME,\
                   PRJ.NAME,\
                   ENTRY_DATE,\
                   ENTRY.COMMENT\
               ORDER BY USR.LAST_NAME ASC,\
                   CUST.NAME,\
                   PRJ.NAME,\
                   ENTRY_DATE;' % days

    cursor.execute(request)
    records = cursor.fetchall()
    return records

def formatRecord(records):
    users = {}
    for lname, fname, customer, project, d, t, comment in sorted(records):
        cname = "%s %s" % (fname, lname)
        entries = users.setdefault(cname, {})
        cust = entries.setdefault(customer, {})
        if not comment:
            comment = ''
        work = (str(d).split(' ')[0], t, comment)
        cust.setdefault(project, []).append(work)

    msg = ''
    for user,customers in users.items():
      msg += "%s:\n" % user
      for customer,projects in customers.items():
         #msg += "* %s:\n" % customer
         for project, works in projects.items():
             msg += "  * %s " % project
             #h = 0
             msgw = ''
             for w in works:
                 # cumulate hours
                 #h += w[1]
                 # if comments
                 if w[2] != '':
                    # replace \n by \t\t"
                    wr = w[2].replace('\n','\n            - ')
                    #msgw += "    (%s h) - %s\n" % (w[1], wr)
                    msgw += "    - %s\n" % wr
             #msg += '(%s h)\n' % h
             msg += '\n'
             msg += '%s\n' % msgw
      msg += "--------------------------------------\n\n"
    return msg

if __name__ == "__main__":
    usage = 'Usage: %prog [options]\n'\
            '    Creates a report from eHour DB and send it by e-mail.'
    version = 'ehour-report v%s' % VERSION
    optparser = OptionParser(usage=usage, version=version, description=version)
    optparser.add_option('-c', '--config', dest='config_file',
                         default='ehour-report.cfg', help="Configuration file.")
    (options, args) = optparser.parse_args(sys.argv[1:])

    try:
        # Read config file with all options needed
        cparser = ConfigParser()
        cparser.read(options.config_file)
        # Only postgresql is supported yet
        if 'postgresql' != cparser.get('database', 'type'):
            print "Only postresql is supported at this stage"
            exit(1)
        # Connet to the database
        cursor = connectSql(cparser.get('database', 'host'),
                            cparser.get('database', 'dbname'),
                            cparser.get('database', 'user'),
                            cparser.get('database', 'password'))
        if cursor:
            records = reqSql(cursor, cparser.get('report', 'days'))
            if records:
               msg = formatRecord(records)
               weeknum = "Y%sW%s" % (time.strftime("%y"), time.strftime("%W"))
               sendTextMail(cparser.get('mail', 'server'),
                            cparser.get('mail', 'sender'),
                            cparser.get('mail', 'rcpt'), weeknum, msg)
            else:
               print "No records found!"
        else:
            print "Cannot connect to DB"
    except Exception, e:
        print >> sys.stderr, 'Error: %s' % e
        exit(1)
