# Database manager using telegram bot and streamlit

## Installation and running
In settings.txt you should write your telegram api token, desired password for admin and allowed commands for mongosh (the last one should be written as list in python).

Streamlit is running via sh file, if you have problems like `sh: ./run_streamlit.sh: Permission denied` you should probably change permissions, the following will tell you how:

Change Permissions:

1. Open your terminal.
2. Navigate to the directory where your run_streamlit.sh script is located.
3.Run the following command to change the permissions:
  ```bash
  chmod +x run_streamlit.sh
  ```

## About mongodb
mongosh is connected to the localhost by default, you can change it manually in bot_handler.py and streamlit_app.py.
