from flask import Flask, request
from flask_mail import Mail, Message

app = Flask(__name__)

app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = "gan.shmuel.bc.16@gmail.com"
app.config['MAIL_PASSWORD'] = [REDACTED]

devops_team_lead = "Eliran Ben Shitrit"

devops_team = {
    "Eliran Ben Shitrit": "Eliranbenshtrit@gmail.com"
}

mail = Mail(app)

def send_email(message, emails_list):
    email = Message(message, sender="dev@gmail.com",
                    recipients=emails_list)
    mail.send(email)


@app.route('/log', methods=['POST'])
def log():
    data = request.get_json()

    pusher_name = "{}".format(data['pusher']['name'])
    email_dest = []

    if pusher_name in devops_team:
        email_dest.append(devops_team[devops_team_lead])
        if pusher_name != devops_team_lead:
            email_dest.append(devops_team[pusher_name])

    message = "hey {} your test result is...".format(pusher_name)

    send_email(message, email_dest)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8084, threaded=True, debug=True)
