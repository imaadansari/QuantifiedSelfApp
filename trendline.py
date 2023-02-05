import matplotlib.pyplot as plt
from app import Tracker_Instance
from datetime import datetime


def make_trendline(user, tracker):
    trackers = Tracker_Instance.query.filter_by(
        user_id=user.user_id, tracker=tracker)

    values = []
    for i in trackers:
        values.append(i.value)
    plt.plot(values)

    filename = f'{datetime.utcnow().strftime("plot%d%m%Y%H%M%S")}.png'
    filename = f"{user.user_id}_"+filename
    file_loc = f"mail/trendlines/{filename}"
    plt.savefig(file_loc)
    plt.close()

    return file_loc
