from app import User, Tracker, Tracker_Instance, db
from fpdf import FPDF
from PIL import Image
from sqlalchemy import func
from datetime import datetime, date
from trendline import make_trendline
import smtplib
from email.message import EmailMessage
import schedule


def get_min_max_avg(tracker, user):
    minval = db.session.query(func.min(Tracker_Instance.value)).filter(
        Tracker_Instance.tracker == tracker, Tracker_Instance.user_id == user.user_id).first()[0]
    maxval = db.session.query(func.max(Tracker_Instance.value)).filter(
        Tracker_Instance.tracker == tracker, Tracker_Instance.user_id == user.user_id).first()[0]
    avgval = db.session.query(func.avg(Tracker_Instance.value)).filter(
        Tracker_Instance.tracker == tracker, Tracker_Instance.user_id == user.user_id).first()[0]

    min_instance = Tracker_Instance.query.filter_by(
        tracker=tracker, value=minval, user_id=user.user_id).first()
    max_instance = Tracker_Instance.query.filter_by(
        tracker=tracker, value=maxval, user_id=user.user_id).first()

    return min_instance, max_instance, avgval


def add_pdf_page(pdf, plot_img, user, tracker, min_instance, avg_val, max_instance):
    image = Image.open(plot_img)
    image = image.resize((600, 300))
    pdf.add_page()
    pdf.set_font("helvetica", size=36)
    pdf.set_font(style="B")
    pdf.cell(0, 11, f'{user.user_id} {tracker} Report', 0, 0, 'C',)
    pdf.ln()
    pdf.set_font("Times", size=20)
    date = datetime.now().strftime("%d/%m/%Y")
    pdf.cell(0, 11, f'{date}', 0, 0, 'C',)
    pdf.ln()
    pdf.ln()

    # Minimum
    pdf.set_font("Times", size=30, style="I")
    pdf.set_text_color(15, 53, 185)
    pdf.cell(0, 11, "Minimum:", 0, 0, "C")
    pdf.ln()

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", size=20)
    pdf.cell(0, 11, f"Value: {min_instance.value}", 0, 0, "C")
    pdf.ln()

    pdf.set_font(style="")
    pdf.cell(0, 11, f"Note: {min_instance.note}", 0, 0, "C")
    pdf.ln()

    pdf.cell(0, 11, f"Timestamp: {min_instance.timestamp}", 0, 0, "C")
    pdf.ln()
    pdf.ln()
    # Average

    pdf.set_font("Times", size=30, style="I")
    pdf.set_text_color(15, 53, 185)
    pdf.cell(0, 11, f"Average:", 0, 0, "C")
    pdf.ln()

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", size=20)
    pdf.cell(0, 11, f"Value: {avg_val}", 0, 0, "C")
    pdf.ln()
    pdf.ln()

    # Maximum
    pdf.set_font("Times", size=30, style="I")
    pdf.set_text_color(15, 53, 185)
    pdf.cell(0, 11, "Maximum:", 0, 0, "C")
    pdf.ln()

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", size=20)
    pdf.cell(0, 11, f"Value: {max_instance.value}", 0, 0, "C")
    pdf.ln()

    pdf.cell(0, 11, f"Note: {max_instance.note}", 0, 0, "C")
    pdf.ln()

    pdf.cell(0, 11, f"Timestamp: {max_instance.timestamp}", 0, 0, "C")
    pdf.ln()
    pdf.ln()

    pdf.image(image, x=0, y=185)

    pdf.set_font("Times", size=30, style="I")
    pdf.set_text_color(15, 53, 185)
    pdf.cell(0, 11, "Trendline:", 0, 0, "C")
    pdf.set_text_color(0, 0, 0)


def send_monthly_report(user, sender_add):
    pdf = FPDF()
    trackers = Tracker.query.filter_by(user_sno=user.sno)
    for tracker in trackers:

        min_instance, max_instance, avgval = get_min_max_avg(
            tracker.tracker, user)
        if min_instance == None:
            continue
        else:
            plot_img = make_trendline(user, tracker.tracker)
            add_pdf_page(pdf, plot_img, user, tracker.tracker,
                         min_instance, avgval, max_instance)

    filename = f'{datetime.utcnow().strftime("%d%m%Y%H%M%S")}.pdf'
    filename = f"{user.user_id}_report_"+filename
    file_loc = f"mail/pdfs/{filename}"
    pdf.output(file_loc)

    msg = EmailMessage()
    msg['Subject'] = "MONTHLY REPORT"
    msg['From'] = sender_add
    msg['To'] = user.email
    msg.set_content(
        f"Hi {user.user_id},\n\nAttached below is your monthly report.\n\nRegards,\nQSA.")
    file = file_loc

    with open(file, 'rb') as f:
        file_data = f.read()
        file_name = f.name

    msg.add_attachment(file_data, maintype='application',
                       subtype='octet-stream', filename=file_name)

    smtp.send_message(msg)
    print(f"report sent to {user.email}")


def send_daily_reminder(user, sender_add):
    msg = EmailMessage()
    msg['Subject'] = "DAILY REMINDER"
    msg['From'] = sender_add
    msg['To'] = user.email
    msg.set_content(
        f"Hi {user.user_id},\n\nDon't forget to login and log your progress today.\n\nRegards,\nQSA.")
    smtp.send_message(msg)
    print(f"reminder sent to {user.email}")


sender_add = input("Enter sender email: ")
pswd = input("Enter Password: ")

smtp = smtplib.SMTP_SSL('smtp.gmail.com', 465)
smtp.login(sender_add, pswd)
print("Login Success...")


def send_mails():
    users = User.query.all()
    for user in users:
        send_daily_reminder(user, sender_add)
        if date.today().day == 1:
            send_monthly_report(user, sender_add)


schedule.every().day.at("12:00").do(send_mails)

while True:
    schedule.run_pending()
