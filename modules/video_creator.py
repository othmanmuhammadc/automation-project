import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from modules.utils import log, retry


@retry(max_attempts=3)
def create_video(script_path, capcut_url, selectors, config, video_path):
    with open(script_path, 'r') as f:
        script_data = json.load(f)

    driver = webdriver.Chrome()
    driver.get(capcut_url)

    try:
        # Select style and voice
        style_option = driver.find_element(By.CSS_SELECTOR, selectors['capcut_style_style_key_1'])
        style_option.click()

        voice_option = driver.find_element(By.CSS_SELECTOR, selectors['capcut_voice_voice_key_1'])
        voice_option.click()

        # Paste the script
        script_input = driver.find_element(By.CSS_SELECTOR, selectors['capcut_script_input'])
        script_input.send_keys(script_data['SCRIPT'])

        # Click generate button
        generate_button = driver.find_element(By.CSS_SELECTOR, selectors['capcut_generate_button'])
        generate_button.click()

        # Wait for video generation
        time.sleep(30)  # Adjust based on expected generation time

        # Click export button
        export_button = driver.find_element(By.CSS_SELECTOR, selectors['capcut_export_button'])
        export_button.click()

        # Set export resolution and format
        resolution_dropdown = driver.find_element(By.CSS_SELECTOR, selectors['capcut_export_resolution_dropdown'])
        resolution_dropdown.click()
        resolution_option = driver.find_element(By.CSS_SELECTOR, selectors['capcut_export_resolution_option_1080p'])
        resolution_option.click()

        framerate_dropdown = driver.find_element(By.CSS_SELECTOR, selectors['capcut_export_framerate_dropdown'])
        framerate_dropdown.click()
        framerate_option = driver.find_element(By.CSS_SELECTOR, selectors['capcut_export_framerate_option_30fps'])
        framerate_option.click()

        # Confirm export
        export_confirm_button = driver.find_element(By.CSS_SELECTOR, selectors['capcut_export_confirm_button'])
        export_confirm_button.click()

        # Wait for download
        time.sleep(10)  # Adjust based on expected download time

    except Exception as e:
        log.error(f"Error creating video: {e}")
    finally:
        driver.quit()




        