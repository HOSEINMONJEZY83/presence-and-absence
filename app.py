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

# ایجاد فونت وزیری
font = QFont("Vazir", 18)  # می‌توانید اندازه فونت را تغییر دهید


def show_message_box(title,message):
    msg_box = QMessageBox()
    msg_box.setWindowTitle(title)
    msg_box.setText(message)

    # تنظیم استایل
    msg_box.setStyleSheet("QLabel { font-size: 18px; font-family: 'Vazir'; }")  # تغییر اندازه و نوع فونت

    msg_box.exec_()

# تابع برای دکمه 1
def button1_action():
    db_path = "./my-database.db"
    # بررسی وجود پایگاه داده
    if not os.path.exists(db_path):
        show_message_box( "خطا", "پایگاه داده وجود ندارد.")
        return
        
    def show_success_message():
        show_message_box("موفقیت آمیز", "بارکد با موفقیت اسکن شد.")

    def show_error_message(message):
        show_message_box( "خطا", message)

    # تابع برای ثبت حضور معلم
    def mark_attendance(teacher_codemeli):
        # تاریخ امروز به فرمت شمسی
        today = jdatetime.date.today()
        today_str = today.strftime("%Y/%m/%d")  # فرمت تاریخ به شکل YYYY/MM/DD

        db_path = "./my-database.db"

        # بررسی وجود پایگاه داده
        if not os.path.exists(db_path):
            show_error_message("پایگاه داده ای وجود ندارد! ابتدا یک پایگاه داده بسازید.")
            return  # خروج از تابع در صورت عدم وجود پایگاه داده

        try:
            # اتصال به دیتابیس
            connection = sqlite3.connect(db_path)
            cursor = connection.cursor()

            # بررسی اینکه آیا معلم با کد وارد شده وجود دارد یا خیر
            cursor.execute("SELECT * FROM teachers WHERE codemeli = ?", (teacher_codemeli,))
            teacher = cursor.fetchone()

            if teacher:
                # بررسی اینکه آیا حضور برای آن معلم در آن روز ثبت شده است یا خیر
                cursor.execute("SELECT * FROM attendance WHERE teacher_codemeli = ? AND date = ?",
                               (teacher_codemeli, today_str))
                attendance_record = cursor.fetchone()

                if attendance_record:
                    show_error_message(f'اطلاعات شما یکبار در تاریخ {today_str} ثبت شده است.')
                else:
                    # ثبت تاریخ و وضعیت حضور در جدول attendance
                    cursor.execute("INSERT INTO attendance (date, teacher_codemeli, present) VALUES (?, ?, ?)",
                                   (today_str, teacher_codemeli, 1))  # 1 به معنی حضور
                    connection.commit()
                    show_success_message()  # نمایش پیام موفقیت‌آمیز
            else:
                show_error_message('کاربری با این QR Code یافت نشد.')

        except sqlite3.Error as e:
            print("Database error:", e)

        finally:
            # بستن اتصال
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    # باز کردن دوربین
    cap = cv.VideoCapture(0)

    while True:
        # خواندن فریم از دوربین
        ret, frame = cap.read()
        if not ret:
            break

        # شناسایی و خواندن کدهای QR
        decoded_objects = decode(frame)

        for obj in decoded_objects:
            # ذخیره متن کد QR در متغیر
            qr_text = obj.data.decode('utf-8')

            # آزاد کردن دوربین و بستن پنجره‌ها
            cap.release()  # آزاد کردن دوربین
            cv.destroyAllWindows()  # بستن پنجره‌ها

            # ثبت حضور معلم
            mark_attendance(qr_text)

            # خروج از برنامه
            break

        # نمایش فریم
        cv.imshow('QR Code Reader', frame)

        # خروج از حلقه با فشردن کلید 'q'
        if cv.waitKey(1) & 0xFF == ord('q'):
            break

    # آزاد کردن دوربین و بستن پنجره‌ها
    cap.release()
    cv.destroyAllWindows()

# تابع برای دکمه 2
def button2_action():
    def generate_attendance_report():
        db_path = "./my-database.db"

        # بررسی وجود پایگاه داده
        if not os.path.exists(db_path):
            show_message_box( "خطا", "پایگاه داده وجود ندارد.")
            return

        # اتصال به دیتابیس
        try:
            connection = sqlite3.connect(db_path)

            # نوشتن SQL برای دریافت داده‌ها
            query_check_data = "SELECT COUNT(*) FROM attendance"
            cursor = connection.cursor()
            cursor.execute(query_check_data)
            data_count = cursor.fetchone()[0]

            if data_count == 0:
                show_message_box( "خطا", "داده‌ای برای گزارش وجود ندارد.")
                return

            # نوشتن SQL برای دریافت داده‌ها
            query = '''
            SELECT t.name, t.lastname, t.fathername, t.codemeli, a.date
            FROM attendance a
            JOIN teachers t ON a.teacher_codemeli = t.codemeli
            ORDER BY a.date
            '''

            # خواندن داده‌ها از دیتابیس
            df = pd.read_sql_query(query, connection)

            # ذخیره داده‌ها در فایل اکسل
            output_file = 'attendance_report.xlsx'
            df.to_excel(output_file, index=False, engine='openpyxl')

            show_message_box( "موفقیت آمیز", f"گزارش در فایل {output_file} با موفقیت انجام شد.")

        except sqlite3.Error as e:
            show_message_box( "خطا", f"خطا در اتصال به دیتابیس: {e}")

        except Exception as e:
            show_message_box( "خطا", f"خطا در تولید گزارش: {e}")

        finally:
            # بستن اتصال
            if connection:
                connection.close()

    # فراخوانی تابع برای تولید گزارش
    generate_attendance_report()

# تابع برای دکمه 3
def button3_action():
    def create_database():
        # اتصال به پایگاه داده (این عمل در هر دو حالت انجام می‌شود)
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()

        # ایجاد جدول معلم‌ها
        cursor.execute('''
           CREATE TABLE IF NOT EXISTS teachers (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               name TEXT NOT NULL,
               lastname TEXT NOT NULL,
               fathername TEXT NOT NULL,
               codemeli INTEGER UNIQUE NOT NULL
           )
           ''')

        # ایجاد جدول تاریخ‌ها
        cursor.execute('''
           CREATE TABLE IF NOT EXISTS attendance (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               date DATE NOT NULL,
               teacher_codemeli TEXT,
               present INTEGER DEFAULT 0,
               FOREIGN KEY (teacher_codemeli) REFERENCES teachers(codemeli)
           )
           ''')

        # ذخیره تغییرات و بستن اتصال
        connection.commit()
        connection.close()

        show_message_box( 'موفقیت آمیز', 'پایگاه داده ایجاد شد.')

        # بررسی وجود پایگاه داده

    db_path = './my-database.db'
    if os.path.exists(db_path):
        show_message_box( 'خطا', 'یک پایگاه داده وجود دارد. برای ایجاد پایگاه داده جدید ، پایگاه داده موجود را پاک کنید.')
    else:
        create_database()  # ایجاد پایگاه داده جدید اگر وجود ندارد


def button4_action():
    db_path = './my-database.db'
    if not os.path.exists(db_path):
        show_message_box('خطا', 'پایگاه داده ای وجود ندارد.')
        return

    # ایجاد یک پنجره جدید برای افزودن معلم
    add_teacher_window = QDialog()
    add_teacher_window.setWindowTitle("افزودن معلم")
    add_teacher_window.setFixedSize(500, 270)  # اندازه ثابت برای پنجره افزودن معلم

    layout = QFormLayout()
    add_teacher_window.setLayout(layout)

    # تنظیم فونت وزیری
    font = QFont("Vazir", 12)  # فونت وزیری با اندازه 12

    # ایجاد برچسب و ورودی برای نام معلم
    label_name = QLabel(":نام معلم")
    label_name.setFont(font)  # تنظیم فونت
    entry_name = QLineEdit()
    entry_name.setFont(font)  # تنظیم فونت ورودی
    entry_name.setFixedHeight(40)  # افزایش ارتفاع ورودی
    layout.addRow(label_name, entry_name)

    # ایجاد برچسب و ورودی برای نام خانوادگی معلم
    label_lastname = QLabel(":نام خانوادگی معلم")
    label_lastname.setFont(font)  # تنظیم فونت
    entry_lastname = QLineEdit()
    entry_lastname.setFont(font)  # تنظیم فونت ورودی
    entry_lastname.setFixedHeight(40)  # افزایش ارتفاع ورودی
    layout.addRow(label_lastname, entry_lastname)

    # ایجاد برچسب و ورودی برای نام پدر معلم
    label_fathername = QLabel(":نام پدر معلم")
    label_fathername.setFont(font)  # تنظیم فونت
    entry_fathername = QLineEdit()
    entry_fathername.setFont(font)  # تنظیم فونت ورودی
    entry_fathername.setFixedHeight(40)  # افزایش ارتفاع ورودی
    layout.addRow(label_fathername, entry_fathername)

    label_codemeli = QLabel(":کد ملی معلم")
    label_codemeli.setFont(font)  # تنظیم فونت
    entry_codemeli = QLineEdit()
    entry_codemeli.setFont(font)  # تنظیم فونت ورودی
    entry_codemeli.setFixedHeight(40)  # افزایش ارتفاع ورودی
    layout.addRow(label_codemeli, entry_codemeli)

    # دکمه برای ثبت معلم
    def add_teacher():
        name = entry_name.text()
        lastname = entry_lastname.text()
        fathername = entry_fathername.text()
        codemeli = entry_codemeli.text()

        # بررسی اینکه آیا هر یک از ورودی‌ها خالی است
        if not name:
            show_message_box("خطا", "نام معلم وارد نشده است.")
            add_teacher_window.reject()  # بستن پنجره افزودن معلم
            return
        if not lastname:
            show_message_box("خطا", "نام خانوادگی معلم وارد نشده است.")
            add_teacher_window.reject()  # بستن پنجره افزودن معلم
            return
        if not fathername:
            show_message_box("خطا", "نام پدر معلم وارد نشده است.")
            add_teacher_window.reject()  # بستن پنجره افزودن معلم
            return
        if not codemeli:
            show_message_box("خطا", "کد ملی معلم وارد نشده است.")
            add_teacher_window.reject()  # بستن پنجره افزودن معلم
            return
        if not codemeli.isdigit():
            show_message_box("خطا", "کد ملی باید فقط شامل اعداد باشد.")
            add_teacher_window.reject()  # بستن پنجره افزودن معلم
            return
        if len(codemeli) > 10 or len(codemeli) < 10:  # بررسی اینکه کد ملی 10 رقم باشد
            show_message_box("خطا", "کد ملی باید 10 رقم باشد.")
            add_teacher_window.reject()  # بستن پنجره افزودن معلم
            return
        if not name.isalpha():
            show_message_box("خطا", "نام معلم باید فقط شامل حروف باشد.")
            add_teacher_window.reject()  # بستن پنجره افزودن معلم
            return
        if not lastname.isalpha():
            show_message_box("خطا", "نام خانوادگی معلم باید فقط شامل حروف باشد.")
            add_teacher_window.reject()  # بستن پنجره افزودن معلم
            return
        if not fathername.isalpha():
            show_message_box("خطا", "نام پدر معلم باید فقط شامل حروف باشد.")
            add_teacher_window.reject()  # بستن پنجره افزودن معلم
            return

        try:
            connection = sqlite3.connect(db_path)
            cursor = connection.cursor()


            # اضافه کردن معلم به دیتابیس‭
            cursor.execute('''
                    INSERT INTO teachers (name, lastname, fathername, codemeli) VALUES (?, ?, ?, ?)
                    ''', (name, lastname, fathername, codemeli))

            connection.commit()
            show_message_box("موفقیت", "اطلاعات معلم با موفقیت اضافه شد.")

            # بررسی وجود پوشه qr_codes و ایجاد آن در صورت عدم وجود
            qr_folder = 'qr_codes'
            if not os.path.exists(qr_folder):
                os.makedirs(qr_folder)

            # ایجاد QR Code
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
            img.save(qr_filename)  # ذخیره QR Code در پوشه qr_codes

            show_message_box("موفقیت", "فایل QRCode با موفقیت در مسیر " + qr_filename + " ذخیره شد.")

            add_teacher_window.accept()  # بستن پنجره پس از موفقیت

        except sqlite3.Error as e:
            show_message_box("خطا", f"خطا در اضافه کردن اطلاعات معلم : {e}")

        finally:
            if connection:
                connection.close()

    # دکمه برای ثبت معلم
    add_button = QPushButton("ثبت معلم")
    add_button.setFont(font)  # تنظیم فونت
    add_button.clicked.connect(add_teacher)
    layout.addRow(add_button)

    # دکمه برای بستن پنجره
    close_button = QPushButton("بستن")
    close_button.setFont(font)  # تنظیم فونت
    close_button.clicked.connect(add_teacher_window.reject)
    layout.addRow(close_button)

    add_teacher_window.exec_()  # نمایش پنجره

def button5_action():
    sys.exit()

# ایجاد پنجره اصلی
app = QApplication(sys.argv)
main_window = QWidget()
main_window.setWindowTitle("فرم حضور و غیاب")
main_window.setFixedSize(310, 430)  # اندازه ثابت برای پنجره اصلی

# تنظیم فونت برای پنجره اصلی
main_window.setFont(font)

# ایجاد دکمه‌ها
layout = QVBoxLayout()

button1 = QPushButton('حضور و غیاب')
button1.setFont(font)  # تنظیم فونت
button1.clicked.connect(button1_action)
layout.addWidget(button1)

button2 = QPushButton('گزارش گیری')
button2.setFont(font)  # تنظیم فونت
button2.clicked.connect(button2_action)
layout.addWidget(button2)

button3 = QPushButton('ایجاد پایگاه داده')
button3.setFont(font)  # تنظیم فونت
button3.clicked.connect(button3_action)
layout.addWidget(button3)


button4 = QPushButton('اضافه کردن یک معلم')
button4.setFont(font)  # تنظیم فونت
button4.clicked.connect(button4_action)
layout.addWidget(button4)

button5 = QPushButton('خروج')
button5.setFont(font)  # تنظیم فونت
button5.clicked.connect(button5_action)
layout.addWidget(button5)


main_window.setLayout(layout)
main_window.show()

# اجرای حلقه اصلی
sys.exit(app.exec_())
