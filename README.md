# ehour-report

## Description

Basic script that sends activity iby e-mail from eHour database.

See http://www.ehour.nl for more information.

## Requirements

* a working e-mail server
* Python >= 2.6

### Python modules

* psycopg2
* smtplib

## Usage

    $ ./ehour-report.py -c ehour-report.cfg

### Help

    $ ./ehour-report.py -h
    Usage: ehour-report.py [options]
        Creates a report from eHour DB and send it by e-mail.

    ehour-report v0.1

    Options:
          --version             show program's version number and exit
          -h, --help            show this help message and exit
          -c CONFIG_FILE, --config=CONFIG_FILE
                                Configuration file.

## License

See LICENSE file

