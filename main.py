from io import StringIO
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email import charset
from email.generator import Generator
from bs4 import BeautifulSoup
from datetime import datetime
import smtplib
import getpass
import requests
import schedule
import time
import os

def sendNotificationMail(fromEmail, toEmail, password, book):

    subject = u'Raamatut saab nĆ¼Ć¼d laenutada!'
    text = ('Soovisid teadet, kui raamatut saab laenutada. NĆ¼Ć¼d on see aeg kĆ¤es!' +
            '\n\nRaamat, mille kohta infot tahtsid, oli see: \n' + getBookDetails(book))

    #  Python unicode e-mail sending https://gist.github.com/ymirpl/1052094

    # Default encoding mode set to Quoted Printable. Acts globally!
    charset.add_charset('utf-8', charset.QP, charset.QP, 'utf-8')

    # 'alternativeā€™ MIME type
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "%s" % Header(subject, 'utf-8')

    # Only descriptive part of recipient and sender shall be encoded, not the email address
    msg['From'] = "\"%s\" <%s>" % (Header(fromEmail, 'utf-8'), fromEmail)
    msg['To'] = "\"%s\" <%s>" % (Header(toEmail, 'utf-8'), toEmail)

    textpart = MIMEText(text, 'plain', 'UTF-8')
    msg.attach(textpart)

    # Create a generator and flatten message object to 'fileā€™
    str_io = StringIO()
    g = Generator(str_io, False)
    g.flatten(msg)

    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login(fromEmail, password)
    s.sendmail(fromEmail, toEmail, str_io.getvalue())
    s.quit()

def getBookDetails(url):
    r  = requests.get(url)
    data = r.text
    soup = BeautifulSoup(data, 'lxml')

    links = soup.select('.additionalCopiesNav')
    bookDataView = links[0].a.get('href')

    r  = requests.get(bookDataView)
    data = r.text
    soup = BeautifulSoup(data, 'lxml')

    bibInfoLabels = soup.select('.bibInfoLabel')
    bibInfoData = soup.select('.bibInfoData')

    bookData = (bibInfoLabels[0].get_text() + ': ' + bibInfoData[0].get_text().strip() + '\n' +
               bibInfoLabels[1].get_text() + ': ' + bibInfoData[1].get_text().strip() + '\n')

    r.close()

    return bookData

def checkForBooksInLibrary():

    booksFile = open('books.txt')
    books = booksFile.readlines()

    for book in books:
        r  = requests.get(book)
        data = r.text
        soup = BeautifulSoup(data, 'lxml')
        bibItems = soup.select('.bibItemsEntry')

        tlnKR = 0

        for bibItem in bibItems:
            if bibItem.a.get_text() == 'TlnKR kojulaenutus':
                tlnKR += 1
                if bibItem.get_text().find('KOHAL') == -1:
                    print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' Raamat on raamatukogus olemas, aga praegu ei saa seda laenutada.')
                else:
                    sendNotificationMail(fromEmail, toEmail, password, book)
                    books.remove(book)
                    print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' Teavitus saadetud!')

        if tlnKR == 0:
            print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' Tallinna keskraamatukogu kojulaenutuses ei ole seda raamatut.')

    booksFile.close()

fromEmail = input('Sisesta Gmaili aadress, millelt teavitus saata. \n')
toEmail = input('Sisesta e-posti aadress, millele teavitus saata. \n')
password = getpass.getpass('Sisesta saatja Gmaili salasĆµna. \n')

checkForBooksInLibrary()

schedule.every(3).hours.do(checkForBooksInLibrary)

while True:
    schedule.run_pending()
    time.sleep(30)
