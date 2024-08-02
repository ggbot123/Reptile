from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
import logging
import csv

current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
# Create a logger object
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create a file handler with UTF-8 encoding
file_handler = logging.FileHandler(f".\\log\\log_{current_time}.log", encoding='utf-8')
file_handler.setLevel(logging.INFO)

# Create a formatter and set it for the file handler
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add the file handler to the logger
logger.addHandler(file_handler)

# Optionally, add a console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# 设置Edge选项
edge_options = EdgeOptions()
edge_options.add_argument("--headless")  # 无头模式
edge_options.add_argument("--disable-gpu")

# 初始化Edge webdriver
driver = webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()), options=edge_options)

def fetch_data_for_date(date_str):
    # 访问网页
    url = 'https://bond.sse.com.cn/data/statistics/overview/bondow/'
    driver.get(url)
    # 设置日期并触发日期选择器（假设日期输入框的ID为"tDate"）
    date_script = f"""
    document.getElementById('tDate').removeAttribute('readonly');
    document.getElementById('tDate').value = '{date_str}';
    """
    print(date_script)
    # time.sleep(2)  # 等待2秒钟
    driver.execute_script(date_script)

    # 点击查询按钮（假设查询按钮的类名为"search-btn"）
    search_button = driver.find_element(By.CLASS_NAME, "search-btn")
    search_button.click()

    # 等待表格加载（假设表格类名为"bond_details_table"）
    try:
        WebDriverWait(driver, 80).until(
            EC.presence_of_element_located((By.CLASS_NAME, "bond_details_table"))
        )
        # 或者等待表格中某个特定的元素加载
        WebDriverWait(driver, 80).until(
            EC.presence_of_element_located((By.XPATH, "//table[contains(@class, 'bond_details_table')]//tr"))
        )
    except Exception as e:
        logging.info("Table did not load in time:", e)
        driver.quit()
    time.sleep(1)  # 等待5秒钟，确保表格完全加载

    # 获取页面内容
    web_content = driver.page_source
    logging.info(web_content)

    # 解析HTML
    soup = BeautifulSoup(web_content, 'html.parser')

    # 定位到包含数据的表格
    table = soup.find('table', class_='bond_details_table')

    if table:
        headers = [th.text.strip() for th in table.find_all('th')]
        data = []
        for tr in table.find_all('tr', class_='data'):
            row = [td.text.strip() for td in tr.find_all('td')]
            print(row)
            data.append(row)
        # 输出结果
        print("Headers:", headers)
        for row in data:
            print(row)
        return headers, data
    else:
        print("Table not found.")
        logging.error(f"Table not found for date {date_str}.")
        return None

if __name__ == '__main__':
    # 设置查询日期范围
    start_date = datetime(2020, 1, 1)  # 起始日期
    end_date = datetime(2024, 8, 1)    # 结束日期
    current_date = start_date

    # 保存数据到文件
    filename = '[200101-240801]spot_bond_market_data.csv'
    all_data = []

    # 查询每个日期的数据
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        print(f"Fetching data for date: {date_str}")
        result = fetch_data_for_date(date_str)
        
        if result:
            headers, data = result
            all_data.append((date_str, headers, data))
        
        current_date += timedelta(days=1)  # 移动到下一个日期
    
    # 保存所有数据到CSV文件
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # 写入表头
        writer.writerow(["Date"] + all_data[0][1])  # 添加日期列
        # 写入数据
        for date_str, headers, data in all_data:
            for row in data:
                writer.writerow([date_str] + row)


    # 关闭webdriver
    driver.quit()