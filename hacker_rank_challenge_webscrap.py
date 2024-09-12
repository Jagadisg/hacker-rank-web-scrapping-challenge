from selenium.webdriver.common.by import By
from loguru import logger
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import undetected_chromedriver as uc

# Initialize Chrome service and options
service = Service()
options = uc.ChromeOptions()
options.add_argument("--window-size=1920,1080")
options.add_argument("--log-level=3")
options.add_argument("--lang=en_US")
options.add_argument("disable-infobars")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--start-maximized")

driver = uc.Chrome(service=Service(), options=options)


def count_by_character(driver=driver):    
    try:
        logger.info("Starting the process on Dailymotion URL")
        driver.get("https://www.dailymotion.com/tseries2")
        
        time.sleep(10) 
        logger.info("Page loaded successfully")

        initial_count = len(driver.find_elements(By.XPATH, "//a[@data-testid='video-card']"))
        logger.info(f"Initial video card count: {initial_count}")

        for i in range(9):
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                logger.info(f"Scroll down iteration {i+1}")
                time.sleep(2)

                driver.execute_script("window.scrollBy(0, -200);")
                logger.info(f"Scrolled up slightly after iteration {i+1}")

                WebDriverWait(driver, 120).until(
                    lambda driver: len(driver.find_elements(By.XPATH, "//a[@data-testid='video-card']")) > initial_count
                )
                logger.info(f"New video cards loaded after scroll {i+1}")

                initial_count = len(driver.find_elements(By.XPATH, "//a[@data-testid='video-card']"))
                logger.info(f"Updated video card count: {initial_count}")

                if initial_count >= 500:
                    logger.info("500 video cards reached, stopping scroll")
                    break
            except Exception as e:
                logger.error(f"Error during scrolling or waiting in iteration {i+1}: {e}")
                break  

        video_card = driver.find_elements(By.XPATH, "//a[@data-testid='video-card']")
        dic = {}

        for i in range(len(video_card)):
            vedio_id = video_card[i].get_attribute("href").split("/")[-1]
            
            try:
                [dic.update({ch: dic.get(ch, 0) + 1}) for id in vedio_id for ch in id if not ch.isdigit()]
                logger.info(f"Processed video {i+1}/{len(video_card)}: {vedio_id}")
            except Exception as e:
                logger.error(f"Error processing video {i+1}: {e}")
            
            if i == 500:
                logger.info("500 video cards processed, stopping")
                break
        
        return dic

    except Exception as e:
        logger.error(f"An error occurred in the main function: {e}")
        return {}

    finally:
        driver.quit()
        logger.info("Browser closed successfully")

try:
    result = count_by_character(driver=driver)
    logger.info(f"Final result: {result}")
except Exception as e:
    logger.error(f"Error in execution: {e}")
