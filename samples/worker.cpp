/**
 * @file worker.cpp
 * @author Xuhua Huang
 * @brief
 *
 * g++ -c worker.cpp -o worker.exe -std=c++2a -Wall -Wextra -O3
 *
 * @version 0.1
 * @date 2025-02-25
 *
 * @copyright Copyright (c) 2025
 *
 */

#include <atomic>
#include <chrono>
#include <iostream>
#include <thread>
// #include <opencv2/opencv.hpp>

class WorkerThread {
public:
    WorkerThread(int interval)
        : interval(interval)
        , running(true) {}

    void start() { workerThread = std::thread(&WorkerThread::run, this); }

    void stop() {
        running = false;
        if (workerThread.joinable()) {
            workerThread.join();
        }
    }

    ~WorkerThread() { stop(); }

private:
    int               interval;
    std::atomic<bool> running;
    std::thread       workerThread;

    void run() {
        while (running) {
            std::cout << "Thread is running..." << "\n";
            std::this_thread::sleep_for(std::chrono::seconds(interval));
        }
    }
};

int main() {
    WorkerThread worker(2);
    worker.start();

    while (true) {
        std::cout << "Working from main" << "\n";

        // if (cv::waitKey(1) == 27) { // ESC key
        if (std::cin.get() == 27) {
            std::cout << "ESC key pressed" << "\n";
            break;
        }
    }

    worker.stop();
    return 0;
}
