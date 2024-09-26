from multiprocessing import Process
import os


def run_streamlit():
    os.system("./run_streamlit.sh")


def run_bot():
    os.system("python run_bot.py")


if __name__ == '__main__':
    # Create processes
    streamlit_process = Process(target=run_streamlit)
    bot_process = Process(target=run_bot)

    # Start processes
    streamlit_process.start()
    bot_process.start()

    # Join processes
    streamlit_process.join()
    bot_process.join()
