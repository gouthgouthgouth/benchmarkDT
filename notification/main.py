import csv
from datetime import datetime
from flask import Flask, request

app = Flask(__name__)

file_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
file_name = file_datetime + "_notification.csv"

with open(file_name, "w") as f:
    writer = csv.writer(f)
    writer.writerow(["notification_timestamp", "entity_id", "a"])

@app.route('/notify', methods=['POST'])
def notify():
    payload = request.get_json()
    notified_at = payload.get("notification", {}).get("notifiedAt")

    #TODO to complete here
    entity_id = "entity_id"
    a = "a"

    print(f"Notification reçue à : {notified_at}")
    with open(file_name, "a") as f:
        writer = csv.writer(f)
        writer.writerow([notified_at, entity_id, a])
    return "", 204

if __name__ == '__main__':
    app.run(port=3000)
