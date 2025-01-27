import sys
import sqlite3
import pandas as pd
import qrcode
import os
import jdatetime
from pyzbar.pyzbar import decode
import cv2 as cv
from PySide2.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QMessageBox, QLineEdit, QLabel, QDialog, QFormLayout
from PySide2.QtGui import QFont

font = QFont("Vazir", 18)


def show_message_box(title,message):
    msg_box = QMessageBox()
    msg_box.setWindowTitle(title)
    msg_box.setText(message)

    msg_box.setStyleSheet("QLabel { font-size: 18px; font-family: 'Vazir'; }")

    msg_box.exec_()

def button1_action():
    db_path = "./my-database.db"
    if not os.path.exists(db_path):
        show_message_box( "خطا", "پایگاه داده وجود ندارد.")
        return
        
    def show_success_message():
        show_message_box("موفقیت آمیز", "بارکد با موفقیت اسکن شد.")

    def show_error_message(message):
        show_message_box( "خطا", message)

    def mark_attendance(teacher_codemeli):
        today = jdatetime.date.today()
        today_str = today.strftime("%Y/%m/%d")

        db_path = "./my-database.db"

        
        if not os.path.exists(db_path):
            show_error_message("پایگاه داده ای وجود ندارد! ابتدا یک پایگاه داده بسازید.")
            return 

        try:
            connection = sqlite3.connect(db_path)
            cursor = connection.cursor()

            cursor.execute("SELECT * FROM teachers WHERE codemeli = ?", (teacher_codemeli,))
            teacher = cursor.fetchone()

            if teacher:
                cursor.execute("SELECT * FROM attendance WHERE teacher_codemeli = ? AND date = ?",
                               (teacher_codemeli, today_str))
                attendance_record = cursor.fetchone()

                if attendance_record:
                    show_error_message(f'اطلاعات شما یکبار در تاریخ {today_str} ثبت شده است.')
                else:
                    cursor.execute("INSERT INTO attendance (date, teacher_codemeli, present) VALUES (?, ?, ?)",
                                   (today_str, teacher_codemeli, 1))
                    connection.commit()
                    show_success_message()
            else:
                show_error_message('کاربری با این QR Code یافت نشد.')

        except sqlite3.Error as e:
            print("Database error:", e)

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    cap = cv.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        decoded_objects = decode(frame)

        for obj in decoded_objects:
            qr_text = obj.data.decode('utf-8')
            cap.release()
            cv.destroyAllWindows()
            mark_attendance(qr_text)
            break
        
        cv.imshow('QR Code Reader', frame)

        if cv.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv.destroyAllWindows()

def button2_action():
    def generate_attendance_report():
        db_path = "./my-database.db"

        if not os.path.exists(db_path):
            show_message_box( "خطا", "پایگاه داده وجود ندارد.")
            return

    
        try:
            connection = sqlite3.connect(db_path)

            
            query_check_data = "SELECT COUNT(*) FROM attendance"
            cursor = connection.cursor()
            cursor.execute(query_check_data)
            data_count = cursor.fetchone()[0]

            if data_count == 0:
                show_message_box( "خطا", "داده‌ای برای گزارش وجود ندارد.")
                return

            query = '''
            SELECT t.name, t.lastname, t.fathername, t.codemeli, a.date
            FROM attendance a
            JOIN teachers t ON a.teacher_codemeli = t.codemeli
            ORDER BY a.date
            '''

            df = pd.read_sql_query(query, connection)

            output_file = 'attendance_report.xlsx'
            df.to_excel(output_file, index=False, engine='openpyxl')

            show_message_box( "موفقیت آمیز", f"گزارش در فایل {output_file} با موفقیت انجام شد.")

        except sqlite3.Error as e:
            show_message_box( "خطا", f"خطا در اتصال به دیتابیس: {e}")

        except Exception as e:
            show_message_box( "خطا", f"خطا در تولید گزارش: {e}")

        finally:
            if connection:
                connection.close()

    generate_attendance_report()

def button3_action():
    def create_database():
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()

        cursor.execute('''
           CREATE TABLE IF NOT EXISTS teachers (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               name TEXT NOT NULL,
               lastname TEXT NOT NULL,
               fathername TEXT NOT NULL,
               codemeli INTEGER UNIQUE NOT NULL
           )
           ''')

        cursor.execute('''
           CREATE TABLE IF NOT EXISTS attendance (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               date DATE NOT NULL,
               teacher_codemeli TEXT,
               present INTEGER DEFAULT 0,
               FOREIGN KEY (teacher_codemeli) REFERENCES teachers(codemeli)
           )
           ''')

        connection.commit()
        connection.close()

        show_message_box( 'موفقیت آمیز', 'پایگاه داده ایجاد شد.')


    db_path = './my-database.db'
    if os.path.exists(db_path):
        show_message_box( 'خطا', 'یک پایگاه داده وجود دارد. برای ایجاد پایگاه داده جدید ، پایگاه داده موجود را پاک کنید.')
    else:
        create_database()


def button4_action():
    db_path = './my-database.db'
    if not os.path.exists(db_path):
        show_message_box('خطا', 'پایگاه داده ای وجود ندارد.')
        return

    add_teacher_window = QDialog()
    add_teacher_window.setWindowTitle("افزودن معلم")
    add_teacher_window.setFixedSize(500, 270)

    layout = QFormLayout()
    add_teacher_window.setLayout(layout)

    font = QFont("Vazir", 12)

    label_name = QLabel(":نام معلم")
    label_name.setFont(font)  
    entry_name = QLineEdit()
    entry_name.setFont(font)  
    entry_name.setFixedHeight(40)  
    layout.addRow(label_name, entry_name)

    
    label_lastname = QLabel(":نام خانوادگی معلم")
    label_lastname.setFont(font)  
    entry_lastname = QLineEdit()
    entry_lastname.setFont(font)  
    entry_lastname.setFixedHeight(40)  
    layout.addRow(label_lastname, entry_lastname)

    
    label_fathername = QLabel(":نام پدر معلم")
    label_fathername.setFont(font)  
    entry_fathername = QLineEdit()
    entry_fathername.setFont(font)  
    entry_fathername.setFixedHeight(40)  
    layout.addRow(label_fathername, entry_fathername)

    label_codemeli = QLabel(":کد ملی معلم")
    label_codemeli.setFont(font)  
    entry_codemeli = QLineEdit()
    entry_codemeli.setFont(font)  
    entry_codemeli.setFixedHeight(40)  
    layout.addRow(label_codemeli, entry_codemeli)

    
    def add_teacher():
        name = entry_name.text()
        lastname = entry_lastname.text()
        fathername = entry_fathername.text()
        codemeli = entry_codemeli.text()

        
        if not name:
            show_message_box("خطا", "نام معلم وارد نشده است.")
            add_teacher_window.reject()  
            return
        if not lastname:
            show_message_box("خطا", "نام خانوادگی معلم وارد نشده است.")
            add_teacher_window.reject()  
            return
        if not fathername:
            show_message_box("خطا", "نام پدر معلم وارد نشده است.")
            add_teacher_window.reject()  
            return
        if not codemeli:
            show_message_box("خطا", "کد ملی معلم وارد نشده است.")
            add_teacher_window.reject()  
            return
        if not codemeli.isdigit():
            show_message_box("خطا", "کد ملی باید فقط شامل اعداد باشد.")
            add_teacher_window.reject()  
            return
        if len(codemeli) > 10 or len(codemeli) < 10:  
            show_message_box("خطا", "کد ملی باید 10 رقم باشد.")
            add_teacher_window.reject()  
            return
        if not name.isalpha():
            show_message_box("خطا", "نام معلم باید فقط شامل حروف باشد.")
            add_teacher_window.reject()  
            return
        if not lastname.isalpha():
            show_message_box("خطا", "نام خانوادگی معلم باید فقط شامل حروف باشد.")
            add_teacher_window.reject()  
            return
        if not fathername.isalpha():
            show_message_box("خطا", "نام پدر معلم باید فقط شامل حروف باشد.")
            add_teacher_window.reject()  
            return

        try:
            connection = sqlite3.connect(db_path)
            cursor = connection.cursor()


            ‭
            cursor.execute('''
                    INSERT INTO teachers (name, lastname, fathername, codemeli) VALUES (?, ?, ?, ?)
                    ''', (name, lastname, fathername, codemeli))

            connection.commit()
            show_message_box("موفقیت", "اطلاعات معلم با موفقیت اضافه شد.")

            
            qr_folder = 'qr_codes'
            if not os.path.exists(qr_folder):
                os.makedirs(qr_folder)

            
            qr_filename = os.path.join(qr_folder, f"{name}_{lastname}_{fathername}.png")
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(codemeli)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            img.save(qr_filename)  
            show_message_box("موفقیت", "فایل QRCode با موفقیت در مسیر " + qr_filename + " ذخیره شد.")

            add_teacher_window.accept()  

        except sqlite3.Error as e:
            show_message_box("خطا", f"خطا در اضافه کردن اطلاعات معلم : {e}")

        finally:
            if connection:
                connection.close()

    
    add_button = QPushButton("ثبت معلم")
    add_button.setFont(font)  
    add_button.clicked.connect(add_teacher)
    layout.addRow(add_button)

    
    close_button = QPushButton("بستن")
    close_button.setFont(font)  
    close_button.clicked.connect(add_teacher_window.reject)
    layout.addRow(close_button)

    add_teacher_window.exec_()  

def button5_action():
    sys.exit()


app = QApplication(sys.argv)
main_window = QWidget()
main_window.setWindowTitle("فرم حضور و غیاب")
main_window.setFixedSize(310, 430)  


main_window.setFont(font)


layout = QVBoxLayout()

button1 = QPushButton('حضور و غیاب')
button1.setFont(font)  
button1.clicked.connect(button1_action)
layout.addWidget(button1)

button2 = QPushButton('گزارش گیری')
button2.setFont(font)  
button2.clicked.connect(button2_action)
layout.addWidget(button2)

button3 = QPushButton('ایجاد پایگاه داده')
button3.setFont(font)  
button3.clicked.connect(button3_action)
layout.addWidget(button3)


button4 = QPushButton('اضافه کردن یک معلم')
button4.setFont(font)  
button4.clicked.connect(button4_action)
layout.addWidget(button4)

button5 = QPushButton('خروج')
button5.setFont(font)  
button5.clicked.connect(button5_action)
layout.addWidget(button5)


main_window.setLayout(layout)
main_window.show()


sys.exit(app.exec_())
