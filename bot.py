from selenium import webdriver
import json
import datetime
import schedule
import time
import csv
from PIL import Image, ImageDraw, ImageFont
from twython import Twython
from secrets import CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_SECRET, FIREBASE_URL
from selenium.webdriver.chrome.options import Options
from firebase import firebase

data = {}

doingWeeklyReport = False
weeklyReportName = ""

twitter = Twython(CONSUMER_KEY, CONSUMER_SECRET,
                  ACCESS_TOKEN, ACCESS_SECRET)

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")

firebase = firebase.FirebaseApplication(FIREBASE_URL, None)

def getFileData():
    try:
        f = open("Last Pull.txt", "r")
        fd = f.read()
        f.close()
        return fd
    except:
        return ""

def setDate(today):
    data = {'date': today}
    # result = firebase.put('/-MIbw9ruO-WoEuJfdK2E','date',data)
    print("Last Pull Date Set: " + today)

def getDate():
    result = firebase.get('/-MIbw9ruO-WoEuJfdK2E','date')
    print("Firebase Date: " + str(result.get("date")))
    return result.get("date")

def setFileData():
    f = open("Last Pull.txt", "w")
    f.write(lastPull)
    f.close()


lastPull = getDate()

def Tweet(new_cases, new_deaths, new_recoveries, overall_cases, date, new_active, hospitalized, total_deaths, tests_done, positive_rate, total_recoveries):
    print("\nStarting tweet")
    try:
        tweet = "Jamaica COVID-19 Update as of "+date+":\n"+new_cases+" New Cases, " + \
            new_deaths+" Deaths, "+new_recoveries + \
                " Recoveries" + "\n\n#JamaicaCOVID19 | @codewhare"
        print(tweet)
        GenerateImage(new_cases, new_deaths[0:3].strip(), new_recoveries, overall_cases, date,
                      new_active, hospitalized, total_deaths, tests_done, positive_rate, total_recoveries)
        print("\n\nTweet sent")
    except Exception as e:
        print(str(e))


def GenerateImage(new_cases, new_deaths, new_recoveries, overall_cases, date, new_active, hospitalized, total_deaths, tests_done, positive_rate, total_recoveries):
    print("Attempting image generation")
    img = Image.open("assets/twitter_post.png")
    draw = ImageDraw.Draw(img)
    fnt = ImageFont.truetype("assets/Inter-Bold.ttf", 48)
    regFont = ImageFont.truetype("assets/Inter-Bold.ttf", 22)
    draw.text((339, 182), date, font=regFont, fill=(255, 255, 255))  # Date
    draw.text((373, 381), new_cases, font=regFont,
              fill=(255, 255, 255))  # Positive New Cases
    draw.text((382, 407), new_deaths, font=regFont,
              fill=(255, 255, 255))  # Death Cases
    draw.text((423, 434), new_recoveries, font=regFont,
              fill=(255, 255, 255))  # New Recoveries
    draw.text((132, 256), new_active, font=fnt,
              fill=(255, 255, 255))  # Total Active Cases
    draw.text((324, 256), overall_cases, font=fnt,
              fill=(255, 255, 255))  # Total Positive Cases
    draw.text((705, 380), hospitalized, font=regFont,
              fill=(255, 255, 255))  # Hospitalized Cases
    draw.text((692, 256), total_deaths, font=fnt,
              fill=(255, 255, 255))  # Total Death Cases
    draw.text((515, 256), total_recoveries, font=fnt,
              fill=(255, 255, 255))  # Total Recover Cases
    draw.text((746, 408), tests_done, font=regFont,
              fill=(255, 255, 255))  # tests done Cases
    draw.text((669, 434), positive_rate, font=regFont,
              fill=(255, 255, 255))  # positivity rate
    img.save('post-out.png')
    print("Image generated")


def get3column(items):
    try:
        count = 0
        key = ""
        value = []

        for item in items:
            text = item.text.replace("\n", " ")
            text = text.strip()
            count = count + 1

            if(count == 1):
                key = text
            if(count == 2):
                value.append(text)
            if(count == 3):
                value.append(text)
                data[key] = value
                count = 0
                key = ""
                value = []

        print("Deaths " + data['Deaths'][0])
        print("Recovered cases " + data['Recovered'][0])
        print("Confirmed cases " + data['Confirmed Cases'][0])
        print("Number Hospitalised " + data['Number Hospitalised'][0])
        print("Active Cases " + data['Active Cases'][1])

        try:
            print("Samples Tested " + data['Samples Tested'][0])
        except:
            print("Samples Tested " + data['New Samples Tested'][0])

        print("\nThere were 3 Columns Today")
    except Exception as e:
        print(str(e))
        print("Failed with 3 columns")


def get4column(items):
    try:
        count = 0
        key = ""
        value = []

        for item in items:
            text = item.text.replace("\n", " ")
            text = text.strip()
            count = count + 1

            if(count == 1):
                key = text
            if(count == 2):
                value.append(text)
            if(count == 3):
                value.append(text)
            if(count == 4):
                value.append(text)
            if(count == 5):
                data[key] = value
                count = 1
                key = text
                value = []

        print("Deaths " + data['Deaths'][0])
        print("Recovered cases " + data['Recovered'][0])
        print("Confirmed cases " + data['Confirmed Cases'][0])
        print("Number Hospitalised " + data['Number Hospitalised'][0])
        print("Active Cases " + data['Active Cases'][1])
        try:
            print("Samples Tested " + data['Samples Tested'][0])
        except:
            print("Samples Tested " + data['New Samples Tested'][0])

        print("\nThere were 4 Columns Today")
    except Exception as e:
        print(str(e))
        print("Failed with 4 columns")
        get3column(items)


def Scrape(offset=1):

    driver = webdriver.Chrome(options=chrome_options)

    try:
        global lastPull
        x = datetime.datetime.now()
        print("\n\n")
        print("Scrape initialized: " + str(x))
        y = x - datetime.timedelta(days=offset)  # Yesterday date")
        today = x.strftime("%x")
        print("Today a " + today)

        if(lastPull != today or doingWeeklyReport):
            urlDate = y.strftime("%A") + "-"+y.strftime("%B") + \
                "-" + y.strftime("%-d")+"-"+y.strftime("%Y")
            print("Last Pull: "+lastPull)
            print("URLDate: " + urlDate)
            print("Today: " + today)

            url = "https://www.moh.gov.jm/covid-19-clinical-management-summary-for-" + urlDate
            url2 = "covid-19-update-for-covid-19-clinical-management-summary-for-" + urlDate
            try:
                driver.get(url)
                items = driver.find_elements_by_tag_name("td")
                print("URL: " + url)
            except:
                driver.get(url2)
                items = driver.find_elements_by_tag_name("td")
                print("URL: " + url2)

            get4column(items)

            date = y.strftime("%B") + " " + y.strftime("%d") + \
                ", "+y.strftime("%Y")

            try:
                testsDone = data['Samples Tested'][0].replace(",", "")
            except:
                testsDone = data['New Samples Tested'][0].replace(",", "")

            positivityRate = str(round(
                (int(data["Confirmed Cases"][0].replace(",", "")) / int(testsDone)) * 100, 2)
            ) + "%"

            print("positivity rate: " + positivityRate)

            h1 = 0
            h2 = 0
            hospitalized = "0"
            activeCases = "0"
            a1 = 0
            a2 = 0

            try:
                if data['Number Hospitalised'][0] != '':
                    h1 = int(data['Number Hospitalised'][0].replace(",", ""))

                if data['Number Hospitalised'][1] != '':
                    h2 = int(data['Number Hospitalised'][1].replace(",", ""))

                if h1 > h2:
                    hospitalized = str(h1)
                else:
                    hospitalized = str(h2)
            except Exception as e:
                print("hospitalized errors...: "+str(e))
                hospitalized = data['Number Hospitalised'][1]

            try:
                if data['Active Cases'][0] != '':
                    a1 = int(data['Active Cases'][0].replace(",", ""))

                if data['Active Cases'][1] != '':
                    a2 = int(data['Active Cases'][1].replace(",", ""))

                if a1 > a2:
                    activeCases = str(a1)
                else:
                    activeCases = str(a2)
            except Exception as e:
                print("active cases errors...: "+str(e))
                activeCases = data['Active Cases'][1]

            print("chadddd "+activeCases)
            print("chadddd "+str(a1) + " " + str(a2))

            print("hospitalized:::: " + hospitalized)
            print("cases:::: " + activeCases)

            if not doingWeeklyReport:
                Tweet(data['Confirmed Cases'][0], data['Deaths'][0], data['Recovered'][0], data['Confirmed Cases']
                      [1], date, activeCases, hospitalized, data['Deaths'][1], testsDone, positivityRate, data['Recovered'][1])

                lastPull = today
                setDate(lastPull)
            else:
                print("doing weekly Report")
                with open(weeklyReportName+'.csv', 'a', newline='') as csvfile:
                    spamwriter = csv.writer(
                        csvfile, delimiter=';', quotechar='|', quoting=csv.QUOTE_NONE
                    )
                    spamwriter.writerow([data['Confirmed Cases'][0], data['Deaths'][0][0:3].strip(), data['Recovered'][0], data['Confirmed Cases']
                                         [1], date, data['Active Cases'][1], hospitalized, data['Deaths'][1], testsDone, positivityRate])
        else:
            print("Scrape already done today... I'm gonna sleep!")
            print("---------------------------------------------")
    except Exception as e:
        print(str(e))
    finally:
        driver.close()


def WeeklyReport():
    global doingWeeklyReport
    global weeklyReportName

    doingWeeklyReport = True

    x = datetime.datetime.now()
    y = x - datetime.timedelta(days=7)
    weeklyReportName = "Week of "+str(y).split(" ")[0]

    # make headers
    with open(weeklyReportName+'.csv', 'a', newline='') as csvfile:
        spamwriter = csv.writer(
            csvfile, delimiter=';', quotechar='|', quoting=csv.QUOTE_NONE
        )
        spamwriter.writerow(['Confirmed Cases', 'Deaths', 'Recovered', 'Confirmed Cases', "Date",
                             'Active Cases', "Hospitalized", 'Overall Deaths', "Tests Done", "Positivity Rate"])

    for x in range(7):
        Scrape(x+1)

    print("Report Created: " + weeklyReportName+".csv")
    doingWeeklyReport = False



Scrape()
schedule.every(1).minutes.do(Scrape)

while True:
    schedule.run_pending()
    time.sleep(1)
