import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from modules.utils import log


def generate_script(prompt, provider_url, selectors, script_path):
    driver = webdriver.Chrome()
    driver.get(provider_url)

    try:
        prompt_field = driver.find_element(By.CSS_SELECTOR, selectors['prompt_textarea'])
        prompt_field.send_keys(prompt)

        send_button = driver.find_element(By.XPATH, selectors['send_button'])
        send_button.click()

        time.sleep(5)  # Adjust based on expected response time
        response_area = driver.find_element(By.XPATH, selectors['response_area_last'])
        response_text = response_area.text

        script_data = parse_response(response_text)
        with open(script_path, 'w') as f:
            json.dump(script_data, f, indent=4)

    except Exception as e:
        log.error(f"Error generating script: {e}")
    finally:
        driver.quit()


def parse_response(response_text):
    sections = response_text.split('\n\n')
    script_data = {
        'SCRIPT': sections[0],
        'TITLE': sections[1],
        'DESCRIPTION': sections[2],
        'KEYWORDS': sections[3].split(',')
    }
    return script_data







