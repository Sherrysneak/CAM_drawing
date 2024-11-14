import cv2
import numpy as np
import tkinter as tk
from threading import Thread
import os

# 初始化全局变量
weight_map = None
base_image = None
sigma = 20  # 高斯模糊半径
increment_value = 0.1  # 每次点击增加的权重值
save_counter = 1  # 保存图片的编号
history_stack = []  # 保存权重图的历史记录

image_path = "img/1.png"  # 输入图片路径

def click_event(event, x, y, flags, param):
    """鼠标点击事件，用于增加点击点的权重，并实时更新CAM图"""
    global weight_map, base_image, sigma, increment_value, history_stack

    if event == cv2.EVENT_LBUTTONDOWN:
        # 保存当前权重图到历史记录栈
        history_stack.append(weight_map.copy())

        # 每次点击在权重图上增加小的权重值
        heatmap = np.zeros((base_image.shape[0], base_image.shape[1]), dtype=np.float32)
        cv2.circle(heatmap, (x, y), radius=15, color=increment_value, thickness=-1)
        heatmap = cv2.GaussianBlur(heatmap, (0, 0), sigmaX=sigma, sigmaY=sigma)

        # 将点击生成的热力添加到整体权重图中
        weight_map += heatmap
        weight_map = np.clip(weight_map, 0, 1)  # 确保权重在[0, 1]之间

        # 实时显示CAM图
        cam_image = apply_cam(base_image, weight_map)
        cv2.imshow("Real-time CAM", cam_image)


def apply_cam(image, weight_map):
    """将生成的权重图叠加到原图上"""
    colormap = cv2.applyColorMap((weight_map * 255).astype(np.uint8), cv2.COLORMAP_JET)
    cam_result = cv2.addWeighted(image, 0.5, colormap, 0.5, 0)
    return cam_result


def save_image():
    """保存当前CAM图像，并确保文件名不覆盖"""
    global save_counter
    cam_image = apply_cam(base_image, weight_map)
    save_path = f"saved_cam_image_{save_counter}.jpg"
    cv2.imwrite(save_path, cam_image)
    print(f"Image saved as {save_path}")
    save_counter += 1


def undo_last_action():
    """撤销上一次的鼠标点击操作"""
    global weight_map, history_stack

    if history_stack:
        weight_map = history_stack.pop()
        cam_image = apply_cam(base_image, weight_map)
        cv2.imshow("Real-time CAM", cam_image)
        print("Last action undone.")
    else:
        print("No actions to undo.")


def update_parameters():
    """从GUI界面获取sigma和increment_value参数的实时更新"""
    global sigma, increment_value
    try:
        sigma = float(sigma_entry.get())
        increment_value = float(increment_value_entry.get())
        print(f"Updated sigma: {sigma}, increment_value: {increment_value}")
    except ValueError:
        print("Please enter valid numbers for sigma and increment_value.")


def start_cam_window():
    """启动OpenCV窗口线程"""
    global weight_map, base_image

    # 读取图像
    base_image = cv2.imread(image_path)
    if base_image is None:
        raise FileNotFoundError("Image not found.")

    # 初始化权重图为零矩阵
    weight_map = np.zeros((base_image.shape[0], base_image.shape[1]), dtype=np.float32)

    # 显示窗口和实时更新的CAM图
    cv2.imshow("Real-time CAM", base_image)
    cv2.setMouseCallback("Real-time CAM", click_event)

    # 主循环：按下 "ESC" 键退出
    while True:
        key = cv2.waitKey(20) & 0xFF
        if key == 27:  # 按 ESC 键退出
            break
    cv2.destroyAllWindows()


def start_gui():
    """启动Tkinter GUI线程"""
    root = tk.Tk()
    root.title("CAM Control Panel")

    # 设置GUI的字体
    font_settings = ("Arial", 12)

    # sigma输入框
    tk.Label(root, text="Sigma:", font=font_settings).grid(row=0, column=0, padx=5, pady=5)
    global sigma_entry
    sigma_entry = tk.Entry(root, font=font_settings)
    sigma_entry.insert(0, str(sigma))
    sigma_entry.grid(row=0, column=1, padx=5, pady=5)

    # increment_value输入框
    tk.Label(root, text="Increment Value:", font=font_settings).grid(row=1, column=0, padx=5, pady=5)
    global increment_value_entry
    increment_value_entry = tk.Entry(root, font=font_settings)
    increment_value_entry.insert(0, str(increment_value))
    increment_value_entry.grid(row=1, column=1, padx=5, pady=5)

    # 更新参数按钮
    update_button = tk.Button(root, text="更新参数", font=font_settings, command=update_parameters)
    update_button.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

    # 保存图像按钮
    save_button = tk.Button(root, text="保存图像", font=font_settings, command=save_image)
    save_button.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

    # 回退按钮
    undo_button = tk.Button(root, text="撤回上一步", font=font_settings, command=undo_last_action)
    undo_button.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

    # 说明区域
    about_text = (
        "使用说明：\n"
        "- 在图像上点击来添加热力区域\n"
        "- Sigma                 高斯模糊半径\n"
        "- Increment Value  单次的权重增量值\n"
    )
    tk.Label(root, text=about_text, font=("Arial", 10), justify="left", wraplength=300).grid(row=5, column=0, columnspan=2, padx=10, pady=10)

    root.mainloop()


if __name__ == "__main__":
    # 启动两个线程：一个用于OpenCV窗口，另一个用于Tkinter GUI
    Thread(target=start_cam_window).start()
    Thread(target=start_gui).start()
