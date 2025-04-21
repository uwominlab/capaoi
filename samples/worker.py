import threading
import time

from cv2 import waitKey


class WorkerThread(threading.Thread):
    """A worker thread that runs a task at a specified interval."""

    def __init__(self, interval=1):
        super().__init__()
        self.interval = interval
        self.running = True  # Control flag for stopping the thread
        self.daemon = True   # Set as daemon so it stops when the main program exits

    def run(self):
        while self.running:
            print("Thread is running...")
            time.sleep(self.interval)

    def stop(self):
        self.running = False


def main():
    # Create and start the thread
    worker = WorkerThread(interval=2)
    worker.start()

    print("Main function is running...")

    # Main program continues
    while True:
        print("Working from main")
        time.sleep(2)
        key = waitKey(1)
        if key == 27:
            break

    worker.stop()   # Gracefully stop the thread
    worker.join()   # Ensure the thread terminates properly


if __name__ == "__main__":
    main()
