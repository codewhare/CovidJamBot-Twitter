import requests
import json
from bs4 import BeautifulSoup
import os, logging, datetime, schedule, time, csv
from PIL import Image, ImageDraw, ImageFont
from twython import Twython
from firebase import firebase
from secrets import CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_SECRET, FIREBASE_URL
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

data = {}
header = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
}

firebase = firebase.FirebaseApplication(FIREBASE_URL, None)

twitter = Twython(CONSUMER_KEY, CONSUMER_SECRET,
                  ACCESS_TOKEN, ACCESS_SECRET)

def getFileData():
    try:
        f = open("Last Pull.txt", "r")
        fd = f.read()
        f.close()
        return fd
    except:
        return ""

def setDate():
    x = datetime.datetime.now()
    today = x.strftime("%x")
    data = {'date': today}
    result = firebase.put('/-MIbw9ruO-WoEuJfdK2E','date',data)
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

def getData():
    global lastPull
    lastPull = getDate()
    x = datetime.datetime.now()
    y = x - datetime.timedelta(days=1)  # Yesterday date
    today = x.strftime("%x")
    url = GetTheLastPost()
    if(url == "NO MATCH"):
        print("Nothing")
    elif(lastPull != today):
        key: ""
        values = []
        index = 0

        try:
            html = requests.get(url, headers=header).text
            soup = BeautifulSoup(html, "html.parser")
            
            for element in soup.find_all('tr'):
                for td in element.find_all('td'):
                    if index == 0:
                        key = td.text.strip()
                    else:
                        values.append(td.text.strip())
                    index += 1
                data[key]= values
                index = 0
                key = ""
                values = []
        except Exception as e:
            print(str(e))
        extractWhatWeCareAbout()
    else:
        print("Scrape already done today... I'm gonna sleep!")
        print("---------------------------------------------")

def ordinal(n):
    return ["th", "st", "nd", "rd"][n%10 if n%10<4 and not (10<n%100<14) else 0]

def GetTheLastPost():
    x = datetime.datetime.now()
    today = x.strftime("%d")

    url = "https://www.moh.gov.jm/updates/coronavirus/covid-19-clinical-management-summary/"
    html = requests.get(url, headers=header).text
    soup = BeautifulSoup(html, "html.parser")

    posts = soup.find_all("span", {"class": "cat-post-time"})

    latest_date = posts[0].text

    links = soup.find_all("a", {"class":"read-more btn btn-default hvr-grow"}) 

    today_date = x.strftime("%B "+str(int(today))+ordinal(int(today))+", %Y")
    if(latest_date != today_date):
        return "NO MATCH"
    else:
        return links[0]['href']
        

def extractWhatWeCareAbout():
    finalData = {}

    offset = 1
    x = datetime.datetime.now()
    y = x - datetime.timedelta(days=offset)  # Yesterday date")

    date = y.strftime("%B") + " " + y.strftime("%d") + \
                ", "+y.strftime("%Y")
    

    try:
        samples = data['Samples Tested'][3]
        hasExcessNumber = len(samples.split(",")) > 1 and len(samples.split(",")[-1]) > 3
        testsDone = samples.replace(",", "")
        if hasExcessNumber:
            testsDone = testsDone[:-1]
    except:
        try:
            samples = data['New Samples Tested'][3]
            hasExcessNumber = len(samples.split(",")) > 1 and len(samples.split(",")[-1]) > 3
            testsDone = samples.replace(",", "")
            if hasExcessNumber:
                testsDone = testsDone[:-1]
        except:
            samples = data['TOTAL TESTS TODAY'][3]
            hasExcessNumber = len(samples.split(",")) > 1 and len(samples.split(",")[-1]) > 3
            testsDone = samples.replace(",", "")
            if hasExcessNumber:
                testsDone = testsDone[:-1]

    print(testsDone)
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
        activeCases = data['Active Cases'][1]

    Tweet(data['Confirmed Cases'][0], data['Deaths'][0], data['Recovered'][0], data['Confirmed Cases']
            [1], date, activeCases, hospitalized, data['Deaths'][1], testsDone, positivityRate, data['Recovered'][1])

def Tweet(new_cases, new_deaths, new_recoveries, overall_cases, date, new_active, hospitalized, total_deaths, tests_done, positive_rate, total_recoveries):
    print("\nStarting tweet")
    try:
        tweet = "Jamaica COVID-19 Update as of "+date+":\n"+new_cases+" New Cases, " + \
            new_deaths[0:3].replace("*","")+" Deaths, "+new_recoveries + \
                " Recoveries" + "\n#GetVaccinated\n#JamaicaCOVID19 | @codewhare"
        print(tweet)
        GenerateImage(new_cases, new_deaths[0:3].replace("*",""), new_recoveries, overall_cases, date,
                      new_active, hospitalized, total_deaths, tests_done, positive_rate, total_recoveries)
        photo = open('post-out.png', 'rb')
        response = twitter.upload_media(media=photo)
        twitter.update_status(status=tweet, media_ids=[response['media_id']])
        print("\n\nTweet sent")
        setDate()
    except Exception as e:
        print(str(e))

def GenerateImage(new_cases, new_deaths, new_recoveries, overall_cases, date, new_active, hospitalized, total_deaths, tests_done, positive_rate, total_recoveries):
    print("Attempting image generation")
    img = Image.open("assets/twitter_post.png")
    draw = ImageDraw.Draw(img)
    fnt = ImageFont.truetype("assets/Inter-Bold.ttf", 64)
    regFont = ImageFont.truetype("assets/Inter-Bold.ttf", 22)
    draw.text((366, 168), date, font=regFont, fill=(255, 255, 255))  # Date
    draw.text((65, 237), new_cases, font=fnt,
              fill=(255, 255, 255))  # Positive New Cases
    draw.text((506, 237), new_deaths, font=fnt,
              fill=(255, 255, 255))  # Death Cases
    draw.text((279, 242), new_recoveries, font=fnt,
              fill=(255, 255, 255))  # New Recoveries
    draw.text((663, 242), new_active, font=fnt,
              fill=(255, 255, 255))  # Total Active Cases
    draw.text((271, 398), overall_cases, font=regFont,
              fill=(255, 255, 255))  # Total Positive Cases
    draw.text((624, 398), hospitalized, font=regFont,
              fill=(255, 255, 255))  # Hospitalized Cases
    draw.text((283, 430), total_deaths, font=regFont,
              fill=(255, 255, 255))  # Total Death Cases
    draw.text((328, 461), total_recoveries, font=regFont,
              fill=(255, 255, 255))  # Total Recover Cases
    draw.text((725, 430), tests_done, font=regFont,
              fill=(255, 255, 255))  # tests done Cases
    draw.text((648, 461), positive_rate, font=regFont,
              fill=(255, 255, 255))  # positivity rate
    img.save('post-out.png')
    print("Image generated")


def weekly_positivity_rate():
    """
    Call this function to calculate the 7 day positivity rate for public and private facilities iff Covid-19 clinical
    summary URLS follow the expected format. Otherwise, the x day positivity rate is calculates where
    x = 7 - number of URLs that did not follow the expected format
    :return: seven_day_positivity_rate, avg_includes_all_seven_days
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    os.environ["WDM_LOG_LEVEL"] = str(logging.WARNING)
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    # Get yesterday's date
    yesterday = datetime.date.today() - datetime.timedelta(2)
    past_week_dates = []
    avg_includes_all_seven_days = True
    for day in range(0, 7):
        past_date = yesterday - datetime.timedelta(day)
        # Format date to match: weekday_name-month-day-year
        past_date_formatted = past_date.strftime("%A") + "-" + past_date.strftime("%B") + "-" + \
            past_date.strftime("%d").lstrip("0") + "-" + past_date.strftime("%Y")
        past_week_dates.append(past_date_formatted)

    # Grab "Confirmed Cases" and "TOTAL TESTS TODAY" for the past seven days
    daily_totals = []
    for date in past_week_dates:
        # Collect table rows for each date
        table_rows = []
        # Construct the URL for  Covid-19 Clinical management summary
        url = "https://www.moh.gov.jm/covid-19-clinical-management-summary-for-" + date
        try:
            driver.get(url)
            # Get the rows in the table
            items = driver.find_elements_by_tag_name("tr")
            for item in items:
                table_rows.append(item.text.replace("\n", " ").split(' '))
            try:
                # Want [{"confirmed_cases":000, "total_tests_today":000}, ...}
                # Indexing is not reliable. Only thing certain is a table with rows
                confirmed_cases = [item for item in table_rows if item[0:2] == ['Confirmed', 'Cases']][0][-2]
                total_tests_today = [item for item in table_rows if item[0:3] == ['TOTAL', 'TESTS', 'TODAY']][0][-1]
            except IndexError:
                print("Erroneous url: ", url)
                print("Oops, looks like the url for that date does not follow the format: weekday_name-month-day-year")
                print("Perhaps add a note * to the total?")
                avg_includes_all_seven_days = False
                continue
            daily_totals.append({"confirmed_cases": int(confirmed_cases.replace(',', '')),
                                 "total_tests_today": int(total_tests_today.replace(',', ''))
                                 })
        except IndexError:
            continue
        except Exception as e:
            print("Unhandled Exception: ", e)
            return
    total_confirmed_cases = sum(item['confirmed_cases'] for item in daily_totals)
    total_tests = sum(item['total_tests_today'] for item in daily_totals)
    seven_day_positivity_rate = (total_confirmed_cases / total_tests) * 100
    return seven_day_positivity_rate, avg_includes_all_seven_days


getData()

schedule.every(1).minutes.do(getData)

while True:
    schedule.run_pending()
    time.sleep(1)
