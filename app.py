import re
import time
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from flask import Flask, jsonify,request
import requests

# Global variables
abc = ""  # This will store the parsed access token
bearer_token = ""
initial_url = ""

# Flask app
app = Flask(__name__)

# Function to initialize Selenium with DevTools Protocol for network monitoring
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    
    # Set up the Service for ChromeDriver
    service = Service(ChromeDriverManager().install())

    # Set up Chrome WebDriver with the options and service
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Enabling the DevTools Protocol to monitor network traffic
    driver.execute_cdp_cmd('Network.enable', {})
    
    return driver

# Function to monitor network traffic and capture the bearer token
def capture_bearer_token(driver):
    global bearer_token

    # Intercept network requests and look for the authorization header in the API call
    def intercept_request(request):
        if "Authorization" in request['headers'] and 'Bearer' in request['headers']['Authorization']:
            authorization = request['headers']['Authorization']
            if authorization.startswith('Bearer '):
                bearer_token = authorization.split(' ')[1]
                print(f"Captured Bearer Token: {bearer_token}")

    # Register the callback to intercept network requests
    driver.request_interceptor = intercept_request

# Function to login to the website, navigate to the next page, and capture the URL with token
def login_and_capture_token():
    global abc, bearer_token, initial_url

    # Start WebDriver
    driver = get_driver()

    # Go to the website (replace with the actual login URL)
    driver.get('https://insurancetoolkits.com/login')

    # Wait for the page to load
    time.sleep(2)

    # Find the username and password fields (modify the selectors as per your form)
    username_field = driver.find_element(By.NAME, 'email')  # Replace with actual field selector
    password_field = driver.find_element(By.NAME, 'password')  # Replace with actual field selector

    # Enter your login credentials
    username_field.send_keys('moetradin@gmail.com')  # Replace with actual username
    password_field.send_keys('qZxj2BbCpXWOhw')  # Replace with actual password
    password_field.send_keys(Keys.RETURN)  # Submit the form
    print("The login is confirmed")

    # Wait for login to complete and for the page with tokens to load
    time.sleep(5)  # Adjust based on the time it takes for the URL to load

    # Capture the URL just before the page redirects (when the token is in the URL)
    initial_url = driver.current_url
    print(f"Captured Initial URL: {initial_url}")

    # Parse the accessToken from the initial URL
    match = re.search(r"accessToken=([^&]+)", initial_url)
    if match:
        abc = match.group(1)  # Extract the value of accessToken
        print(f"Parsed Access Token: {abc}")

    # Now monitor for API calls to capture the bearer token
    capture_bearer_token(driver)

    # Wait for the page to load and redirect (e.g., the final URL without the token in the query string)
    WebDriverWait(driver, 10).until(EC.url_contains("fex/quoter"))
    
    # Capture the redirected URL (final URL)
    final_url = driver.current_url
    print(f"Final URL after redirection: {final_url}")

    # Close the driver
    driver.quit()

# Function to run the Selenium bot periodically to update the `abc` value
def run_periodically():
    while True:
        print("Starting the Selenium bot...")
        login_and_capture_token()
        print(f"Updated Access Token: {abc}")
        
        # Sleep for 20 hours (20 hours * 60 minutes * 60 seconds)
        print("Waiting for 20 hours before updating the token again...")
        time.sleep(20*60*60)

# Flask route to get the current value of `abc`
@app.route('/get_token')
def get_token():
    return jsonify({"accessToken": abc})


@app.route("/")
def home():
    return "Hello, World!"

@app.route('/quote', methods=['POST'])
def quote():
    faceamount = request.json['faceAmount']
    coverageType = request.json['coverageType']
    sex= request.json['sex']
    state = request.json['state']
    age = request.json['age']
# URL to which the API request will be sent
    url = "https://api.insurancetoolkits.com/quoter/"

    # Bearer token for authorization (replace with actual token)
    bearer_token = ""
    # Data to be sent in the body of the request
    payload = {
        "faceAmount": f"{faceamount}",
        "coverageType": f"{coverageType}",
        "sex": f"{sex}",
        "state":f"{state}",
        "age":f"{age}"
    }

    # Headers for the request, including the Authorization header
    headers = {
        "Authorization": f"Bearer {abc}",
        "Content-Type": "application/json"  # Specify that the body is in JSON format
    }

    # Send the POST request with the bearer token and payload
    response = requests.post(url, headers=headers, json=payload)

    # Print the response from the API (status code and body)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")
    return jsonify(response.json())




# Main execution
if __name__ == '__main__':
    # Run the Selenium bot in a separate thread
    selenium_thread = threading.Thread(target=run_periodically, daemon=True)
    selenium_thread.start()

    # Run the Flask app
    app.run()  # use_reloader=False to avoid running the thread twice
