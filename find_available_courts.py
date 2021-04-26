from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.chrome.options import Options
chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(executable_path='/usr/local/bin/chromedriver', options=chrome_options)

driver.get("https://setagaya.keyakinet.net/Web/Home/WgR_ModeSelect")

path_of_select_by_purpose = "/html/body/form/div/div[2]/div/div[2]/div/ul/li[2]"
tab = driver.find_element_by_xpath(path_of_select_by_purpose)
tab.click()

path_of_outdoor_sports = "/html/body/form/div/div[2]/div/div[2]/div/div[2]/div[1]/ul/li[4]"
WebDriverWait(driver, 10).until(
    EC.text_to_be_present_in_element((By.XPATH, path_of_outdoor_sports), "屋外スポーツ"))
button = driver.find_element_by_xpath(path_of_outdoor_sports)
button.click()

path_of_tennis = "/html/body/form/div/div[2]/div/div[2]/div/div[2]/div[2]/div/div/ul/li[1]"
WebDriverWait(driver, 10).until(
    EC.text_to_be_present_in_element((By.XPATH, path_of_tennis), "テニス"))
button = driver.find_element_by_xpath(path_of_tennis)
button.click()
WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located)

search_button = '//*[@id="btnSearchViaPurpose"]'
button = driver.find_element_by_xpath(search_button)
button.click()

WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.ID, "nextpage")))
elements = driver.find_elements_by_class_name('switch-off')
for element in elements:
    if (element.text in ["世田谷公園", "総合運動場", "大蔵第二運動場"]):
        element.click()
element = driver.find_element_by_class_name('next')
element.click()

month_btn= WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.ID, "lblPeriod1month")))
default_days = driver.find_elements_by_class_name("week")
month_btn.click()
driver.find_element_by_id('btnHyoji').click()
WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located)

while True:
    month_days = driver.find_elements_by_class_name("week")
    if len(month_days) > len(default_days):
        break
    else:
        sleep(1)

year_month = driver.find_element_by_class_name('month').text

park_list = driver.find_elements_by_tag_name('h3')
park_list.pop(0)
park_names = [ park.text for park in park_list ]

sundays = driver.find_elements_by_xpath('//*[@class="day sun"]')
holidays = []
for sunday in sundays:
    if '日' in sunday.text:
        continue
    day_week = sunday.text.split('\n')
    holidays.append((day_week[0], day_week[1]))
holidays = set(holidays)
    
park_index = 0
days = []
courts = []
for table in driver.find_elements_by_tag_name('table'):
    data = table.text.split('\n')
    if len(data) < 2:
        continue
    if len(days) == 0:
        index = 1
        while(data[index + 1] in "月火水木金土日"):
            days.append((data[index], data[index + 1]))
            index += 2
    index = 1 + len(days) * 2
    while ((index + len(days)) < len(data)):
        courts.append({
            'park_index': park_index,
            'park_name': park_names[park_index],
            'court_index': len(courts),
            'court_name': data[index]}
        )
        index += 1
        index += len(days)

    park_index += 1

checked = []
previous = []
checking = []

while True:
    previous = checking
    checking = []

    availabilities = driver.find_elements_by_xpath('//*[@class="switch-off" or @class="closed chars2"]')
    while len(availabilities) > 0:
        if availabilities[0].text in ('○', '△', '－', '×', '＊', '休館'):
            break
        availabilities.pop(0)

    available_days = []
    for court in courts:
        start_idx = len(days) * court['court_index']
        for i in range(start_idx, start_idx + len(days)):
            if availabilities[i].text in ('○', '△'):
                day = days[i - start_idx]
                day_number = day[0]
                day_week = "祝" if day in holidays else day[1]
                # print(f'{court["park_name"]}-{court["court_name"]}: {day_number}({day_week}): {availabilities[i].text}')
                driver.execute_script("arguments[0].scrollIntoView(true);", availabilities[i]);
                
                check_key = (court['court_index'], day_number)
                if check_key in previous:
                    availabilities[i].click()
                if check_key not in checked:
                    availabilities[i].click()
                    checked.append(check_key)
                    checking.append(check_key)
                    if len(checking) == 10:
                        break
        if len(checking) == 10:
            break

    if len(checking) == 0:
        break
    
    next_btns = driver.find_elements_by_xpath('//*[@class="next"]')
    next_btns[len(next_btns) - 1].click()

    while True:
        next_btns = driver.find_elements_by_xpath('//*[@class="next"]')
        if len(next_btns) == 1:
            break
        sleep(1)

    tags = driver.find_elements_by_tag_name('thead')
    tables = driver.find_elements_by_xpath('//*[@class="scroll-div clearfix"]')

    for i in range(len(checking)):
        table = tables[i]
        court_index, day_number = checking[i]
        day_and_slots = [ day_or_slot.replace('\n', '') for day_or_slot in table.find_element_by_tag_name('thead').text.split(' ')]
        day = day_and_slots[0]
        slots = day_and_slots[1:]
        slots_available = [False] * len(slots)
        slots_processing = [False] * len(slots)
        tds = table.find_elements_by_tag_name('td')
        j = 0
        for td in tds:
            if j % len(day_and_slots) == 0:
                j += 1
                continue
            slot_index = (j % len(day_and_slots)) - 1
            if td.text == '○':
                slots_available[slot_index] = True
            elif td.text == '':
                slots_processing[slot_index] = True
            j += 1
        court = courts[court_index]
        for j in range(len(slots)):
            if slots_available[j]:
                print(f'{court["park_name"]}-{court["court_name"]} {day} {slots[j]} 空きあり')
            elif slots_processing[j]:
                print(f'{court["park_name"]}-{court["court_name"]} {day} {slots[j]} 取消処理中')

    prev_btns = driver.find_elements_by_xpath('//*[@class="prev"]')
    prev_btns[len(prev_btns) - 1].click()

    while True:
        month_days = driver.find_elements_by_class_name("week")
        if len(month_days) > len(default_days):
            break
        else:
            sleep(1)

driver.close()
