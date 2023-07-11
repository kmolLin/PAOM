import threading
import queue
import time

# 用于存储照片的队列
photo_queue = queue.Queue()

# 线程函数，用于处理照片的储存
def process_photos():
    while True:
        # 从队列中获取照片
        datas = photo_queue.get()

        # 执行照片的储存操作，可以根据需求进行自定义

        # 假设这里是将照片存储到文件系统中
        save_photo_to_file(datas)

        # 标记照片任务完成
        photo_queue.task_done()

# 假设这是保存照片到文件系统的函数
def save_photo_to_file(datas):
    # 执行照片的储存操作
    # ...
    time.sleep(0.1)
    print(f"Saving photo:{datas[0]}, index:{datas[1]}")

# 创建并启动照片处理线程
photo_thread = threading.Thread(target=process_photos)
photo_thread.daemon = True  # 设置线程为守护线程，即主线程退出时自动退出子线程
photo_thread.start()


def capture_new_photo(i):
    return [i, i, i]

# if __name__ == "__main__":
i = 0
# 主循环，持续获取新照片并放入队列
while True:
    i = i + 1
    data = [0, 0, 0]
    # 模拟获取新照片
    new_photo = capture_new_photo(i)

    # 将照片放入队列进行异步处理
    photo_queue.put([new_photo, i])

    # 继续进行其他操作或等待新照片的到来
    # ...
    print(i)
    time.sleep(0.1)
    if i > 50:
        photo_queue.join()
        break