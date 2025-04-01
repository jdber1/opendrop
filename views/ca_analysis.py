from customtkinter import *
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import io
import os
import math

from utils.image_handler import ImageHandler
from utils.config import *
from utils.validators import *
from .helper.theme import get_system_text_color
from .component.CTkXYFrame import *

class CaAnalysis(CTkFrame):
    def __init__(self, parent, user_input_data, **kwargs):
        super().__init__(parent, **kwargs)  
        self.user_input_data = user_input_data

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        
        self.image_handler = ImageHandler()

        self.output = []
        self.angle_images = {}  # Dictionary to store processed images with angle overlay
        
        self.preformed_methods = {key: value for key, value in user_input_data.analysis_methods_ca.items() if value}

        self.table_data = []  # List to store cell references
        self.create_table(parent=self, rows=user_input_data.number_of_frames, columns=len(self.preformed_methods)+1, headers=['Index'] + list(self.preformed_methods.keys()))

        self.images_frame = CTkFrame(self)
        self.images_frame.grid(row=0, column=1, sticky="nsew", padx=15, pady=(10, 0))

        self.current_index = 0
        self.highlight_row(self.current_index)
        self.initialize_image_display(self.images_frame)


    def create_table(self, parent, rows, columns, headers):
        # Create a frame for the table
        table_frame = CTkXYFrame(parent)
        table_frame.grid(row=0, column=0, pady=15, padx=20, sticky='nsew')

        # Create and place header labels
        for col in range(columns):
            header_label = CTkLabel(table_frame, text=headers[col], font=("Roboto", 14, "bold"))
            header_label.grid(row=0, column=col, padx=10, pady=5)

        # Create and place cell labels for each row
        for row in range(1, rows + 1):
            row_data = []
            for col in range(columns):
                text = ""
                if col == 0:
                    text = row
                cell_label = CTkLabel(table_frame, text=text, font=("Roboto", 12))
                cell_label.grid(row=row, column=col, padx=10, pady=5)
                row_data.append(cell_label)  # Store reference to the cell label
            self.table_data.append(row_data)

        self.table_data[len(self.output)][1].configure(text="PROCESSING...")

    def receive_output(self, extracted_data):
        """接收处理结果并显示接触角"""
        self.output.append(extracted_data)
        index = len(self.output) - 1

        for method in extracted_data.contact_angles.keys():
            preformed_method_list = list(self.preformed_methods.keys())
            
            if method in preformed_method_list:
                column_index = preformed_method_list.index(method)+1
                result = extracted_data.contact_angles[method]
                self.table_data[index][column_index].configure(text=f"({result[LEFT_ANGLE]:.2f}, {result[RIGHT_ANGLE]:.2f})")
            else:
                print(f"Unknown method. Skipping the method.")
        
        # 查找并使用已经计算好的数据
        try:
            # 检查是否有接触角数据 - 使用正确的键名'tangent fit'
            if hasattr(extracted_data, 'contact_angles') and 'tangent fit' in extracted_data.contact_angles:
                image_path = self.user_input_data.import_files[index]
                
                # 从contact_angles字典中获取接触角数据
                angles_data = extracted_data.contact_angles['tangent fit']
                
                # 获取左右角度值
                left_angle = angles_data[LEFT_ANGLE] if LEFT_ANGLE in angles_data else angles_data['left angle']
                right_angle = angles_data[RIGHT_ANGLE] if RIGHT_ANGLE in angles_data else angles_data['right angle']
                
                # 尝试从字典中获取接触点和切线数据
                contact_points = None
                tangent_lines = None
                
                # 查找可能的键名
                for key in ['contact points', 'tangent contact points']:
                    if key in angles_data:
                        contact_points = angles_data[key]
                        print(f"在contact_angles字典中找到接触点数据: {key}")
                        break
                
                for key in ['tangent lines', 'tangent tangent lines']:
                    if key in angles_data:
                        tangent_lines = angles_data[key]
                        print(f"在contact_angles字典中找到切线数据: {key}")
                        break
                
                # 检索裁剪区域信息
                drop_region = None
                if hasattr(self.user_input_data, 'drop_region'):
                    drop_region = self.user_input_data.drop_region
                    print(f"找到裁剪区域信息: {drop_region}")
                
                # 创建角度覆盖
                if contact_points is not None and tangent_lines is not None:
                    print(f"创建角度覆盖，使用接触点和切线数据")
                    print(f"接触点: {contact_points}")
                    print(f"切线: {tangent_lines}")
                    
                    self.angle_images[index] = self.create_angle_overlay(
                        image_path, left_angle, right_angle, contact_points, tangent_lines, drop_region
                    )
                    
                    # 更新当前显示
                    if self.current_index == index:
                        self.display_angle_image(index)
                else:
                    print(f"未找到接触点或切线数据")
            else:
                print(f"图像 {index+1} 缺少角度数据")
        except Exception as e:
            print(f"创建角度覆盖时出错: {e}")
            import traceback
            traceback.print_exc()

        if len(self.output) < self.user_input_data.number_of_frames:
            self.table_data[len(self.output)][1].configure(text="PROCESSING...")

    def highlight_row(self, row_index):
        # Reset all rows to default color
        for row in self.table_data:
            for cell in row:
                color = get_system_text_color()
                cell.configure(text_color=color)  # Reset to default background

        # Highlight the specified row
        if 0 <= row_index < len(self.table_data):
            for cell in self.table_data[row_index]:
                cell.configure(text_color="red")  # Change background color to yellow

    def initialize_image_display(self, frame):
        display_frame = CTkFrame(frame)
        display_frame.grid(sticky="nsew", padx=15, pady=(10, 0))

        self.image_label = CTkLabel(display_frame, text="", fg_color="lightgrey", width=400, height=300)
        self.image_label.grid(padx=10, pady=(10, 5))

        file_name = os.path.basename(self.user_input_data.import_files[self.current_index])
        self.name_label = CTkLabel(display_frame, text=file_name)
        self.name_label.grid()

        # Add toggle button for angle display
        self.toggle_frame = CTkFrame(display_frame)
        self.toggle_frame.grid(pady=(5, 0))
        
        self.show_angles_var = IntVar(value=1)
        self.show_angles_cb = CTkCheckBox(self.toggle_frame, text="Show Contact Angles", variable=self.show_angles_var, 
                                         command=self.toggle_angle_display)
        self.show_angles_cb.grid(row=0, column=0, padx=10, pady=5)

        self.image_navigation_frame = CTkFrame(display_frame)
        self.image_navigation_frame.grid(pady=20)

        self.prev_button = CTkButton(self.image_navigation_frame, text="<", command=lambda: self.change_image(-1), width=3)
        self.prev_button.grid(row=0, column=0, padx=5, pady=5)

        self.index_entry = CTkEntry(self.image_navigation_frame, width=5)
        self.index_entry.grid(row=0, column=1, padx=5, pady=5)
        self.index_entry.bind("<Return>", lambda event: self.update_index_from_entry())
        self.index_entry.insert(0, str(self.current_index + 1))

        self.navigation_label = CTkLabel(self.image_navigation_frame, text=f" of {self.user_input_data.number_of_frames}", font=("Arial", 12))
        self.navigation_label.grid(row=0, column=2, padx=5, pady=5)

        self.next_button = CTkButton(self.image_navigation_frame, text=">", command=lambda: self.change_image(1), width=3)
        self.next_button.grid(row=0, column=3, padx=5, pady=5)

        self.load_image(self.user_input_data.import_files[self.current_index])

    def toggle_angle_display(self):
        """Toggle between showing original image and image with angle overlay"""
        self.display_current_image()
    
    def create_angle_overlay(self, image_path, left_angle, right_angle, contact_points, tangent_lines, drop_region=None):
        """创建接触角覆盖图像 - 使用真实的基线(baseline)"""
        try:
            # 打开原始图像
            original_img = Image.open(image_path)
            img = original_img.copy().convert('RGB')
            draw = ImageDraw.Draw(img)
            
            # 提取接触点和处理裁剪区域偏移
            if contact_points is not None:
                # 打印原始接触点和切线信息用于调试
                print(f"原始接触点坐标: 左={contact_points[0]}, 右={contact_points[1]}")
                print(f"原始切线坐标: 左起点={tangent_lines[0][0]}, 左终点={tangent_lines[0][1]}")
                print(f"原始切线坐标: 右起点={tangent_lines[1][0]}, 右终点={tangent_lines[1][1]}")
                
                # 如果有裁剪区域信息，调整坐标
                offset_x = 0
                offset_y = 0
                
                if drop_region is not None:
                    print(f"裁剪区域信息: {drop_region}")
                    
                    # 获取X偏移
                    offset_x = drop_region[0][0]
                    # 由于裁剪问题，Y偏移设为固定值
                    offset_y = 190
                    
                    print(f"应用的坐标偏移: x={offset_x}, y={offset_y}")
                
                # 应用偏移到接触点 - 这些就是baseline的两个端点
                left_point = (float(contact_points[0][0]) + offset_x, float(contact_points[0][1]) + offset_y)
                right_point = (float(contact_points[1][0]) + offset_x, float(contact_points[1][1]) + offset_y)
                
                # 应用偏移到切线，并延长切线
                # 首先计算切线方向向量
                left_dir_x = float(tangent_lines[0][1][0]) - float(tangent_lines[0][0][0])
                left_dir_y = float(tangent_lines[0][1][1]) - float(tangent_lines[0][0][1])
                right_dir_x = float(tangent_lines[1][1][0]) - float(tangent_lines[1][0][0])
                right_dir_y = float(tangent_lines[1][1][1]) - float(tangent_lines[1][0][1])
                
                # 标准化向量
                left_len = math.sqrt(left_dir_x**2 + left_dir_y**2)
                right_len = math.sqrt(right_dir_x**2 + right_dir_y**2)
                
                if left_len > 0:
                    left_dir_x /= left_len
                    left_dir_y /= left_len
                
                if right_len > 0:
                    right_dir_x /= right_len
                    right_dir_y /= right_len
                
                # 设置较长的切线长度
                tangent_length = 80  # 增加切线长度
                
                # 计算延长的切线终点
                left_tangent_start = left_point
                left_tangent_end = (left_point[0] + left_dir_x * tangent_length, 
                                left_point[1] + left_dir_y * tangent_length)
                
                right_tangent_start = right_point
                right_tangent_end = (right_point[0] + right_dir_x * tangent_length, 
                                    right_point[1] + right_dir_y * tangent_length)
                
                print(f"调整后的接触点: 左={left_point}, 右={right_point}")
                
                # 绘制baseline - 直接连接两个接触点
                baseline_width = 2  # 基线宽度
                baseline_color = '#0000FF'  # 蓝色
                
                # 延长baseline
                baseline_extension = 30  # 基线两侧延长的长度
                baseline_dx = right_point[0] - left_point[0]
                baseline_dy = right_point[1] - left_point[1]
                baseline_length = math.sqrt(baseline_dx**2 + baseline_dy**2)
                
                if baseline_length > 0:
                    # 单位方向向量
                    baseline_dx /= baseline_length
                    baseline_dy /= baseline_length
                    
                    # 计算延长后的基线端点
                    baseline_left = (left_point[0] - baseline_dx * baseline_extension, 
                                    left_point[1] - baseline_dy * baseline_extension)
                    baseline_right = (right_point[0] + baseline_dx * baseline_extension, 
                                    right_point[1] + baseline_dy * baseline_extension)
                    
                    # 绘制基线
                    draw.line((baseline_left[0], baseline_left[1], baseline_right[0], baseline_right[1]), 
                            fill=baseline_color, width=baseline_width)
                else:
                    # 如果基线长度为0，直接使用接触点
                    draw.line((left_point[0], left_point[1], right_point[0], right_point[1]), 
                            fill=baseline_color, width=baseline_width)
                
                # 绘制接触点（红色圆点）
                dot_radius = 5
                draw.ellipse((left_point[0]-dot_radius, left_point[1]-dot_radius, 
                            left_point[0]+dot_radius, left_point[1]+dot_radius), fill='red')
                draw.ellipse((right_point[0]-dot_radius, right_point[1]-dot_radius, 
                            right_point[0]+dot_radius, right_point[1]+dot_radius), fill='red')
                
                # 绘制切线（绿色线条）
                draw.line((left_tangent_start[0], left_tangent_start[1], 
                        left_tangent_end[0], left_tangent_end[1]), fill='#00FF00', width=2)
                draw.line((right_tangent_start[0], right_tangent_start[1], 
                        right_tangent_end[0], right_tangent_end[1]), fill='#00FF00', width=2)
                
                # 添加角度标签文本
                try:
                    font = ImageFont.truetype("arial.ttf", 16)
                except:
                    try:
                        font = ImageFont.load_default()
                    except:
                        font = None
                
                # 添加角度文本标签
                left_text = f"θL: {left_angle:.2f}°"
                right_text = f"θR: {right_angle:.2f}°"
                
                # 设置文本位置
                draw.text((left_point[0] - 70, left_point[1] - 25), 
                        left_text, fill='blue', font=font)
                draw.text((right_point[0] + 10, right_point[1] - 25), 
                        right_text, fill='blue', font=font)
                
                return img
            else:
                # 如果没有接触点数据，返回原始图像
                return original_img
                    
        except Exception as e:
            print(f"创建接触角覆盖图时出错: {e}")
            import traceback
            traceback.print_exc()
            return Image.open(image_path)  # 如果出错返回原始图像

    def load_image(self, selected_image):
        """Load and display the selected image."""
        try:
            self.current_image = Image.open(selected_image)
            self.display_current_image()
        except FileNotFoundError:
            print(f"Error: The image file {selected_image} was not found.")
            self.current_image = None

    def display_current_image(self):
        """Display either the original image or the image with angle overlay based on toggle state"""
        if self.show_angles_var.get() == 1 and self.current_index in self.angle_images:
            # Show image with angle overlay
            self.display_angle_image(self.current_index)
        else:
            # Show original image
            self.display_image()

    def display_angle_image(self, index):
        """Display an image with the contact angle overlay"""
        if index in self.angle_images:
            img = self.angle_images[index]
            width, height = img.size
            new_width, new_height = self.image_handler.get_fitting_dimensions(width, height)
            self.tk_image = CTkImage(img, size=(new_width, new_height))
            self.image_label.configure(image=self.tk_image)
            self.image_label.image = self.tk_image
        else:
            # Fall back to original image if no overlay available
            self.display_image()

    def display_image(self):
        """Display the original image without overlay."""
        if self.current_image:
            width, height = self.current_image.size
            new_width, new_height = self.image_handler.get_fitting_dimensions(width, height)
            self.tk_image = CTkImage(self.current_image, size=(new_width, new_height))
            self.image_label.configure(image=self.tk_image)
            # Keep a reference to avoid garbage collection
            self.image_label.image = self.tk_image

    def change_image(self, direction):
        """Change the currently displayed image based on the direction."""
        if self.user_input_data.import_files:
            self.current_index = (
                self.current_index + direction) % self.user_input_data.number_of_frames
            # Load the new image
            self.load_image(
                self.user_input_data.import_files[self.current_index])
            self.update_index_entry()  # Update the entry with the current index
            file_name = os.path.basename(
                self.user_input_data.import_files[self.current_index])
            self.name_label.configure(text=file_name)

            self.highlight_row(self.current_index)

    def update_index_from_entry(self):
        """Update current index based on user input in the entry."""
        try:
            new_index = int(self.index_entry.get()) - \
                1  # Convert to zero-based index
            if 0 <= new_index < self.user_input_data.number_of_frames:
                self.current_index = new_index
                # Load the new image
                self.load_image(
                    self.user_input_data.import_files[self.current_index])
            else:
                print("Index out of range.")
        except ValueError:
            print("Invalid input. Please enter a number.")

        self.update_index_entry()  # Update the entry display

    def update_index_entry(self):
        """Update the index entry to reflect the current index."""
        self.index_entry.delete(0, 'end')  # Clear the current entry
        # Insert the new index (1-based)
        self.index_entry.insert(0, str(self.current_index + 1))