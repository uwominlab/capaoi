"""
Example of an asynchronous task that runs periodically.
"""

import asyncio
import time


TIME_INTERVAL: float = 0.25  # 250ms


async def task():
    """
    Asychronous function to execute.
    """
    print("Task executed at:", time.time())


async def main():
    """
    Blocking polling to exectute the real time task every 250 milliseconds.
    """
    while True:
        start = time.time()
        await task()
        # Run every 250 ms, 4 times per seconds
        await asyncio.sleep(delay=TIME_INTERVAL)
        elapsed_time = time.time() - start
        print(f"Elapsed time: {elapsed_time:.6f} seconds")


if __name__ == "__main__":
    asyncio.run(main())
