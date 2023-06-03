import requests
from flask import Flask

app = Flask(__name__)

html_check_status = ''


@app.route('/monitor')
def monitor():
    global html_check_status
    # html script that refresh the page every 5 sec
    html_check_status = '<meta http-equiv="refresh" content="5">'

    # ports of services
    services = {
        'production-weight': '8081',
        'testing-weight': '8083',
        'production-billing': '8080',
        'testing-billing': '8084'
    }

    paths = ['/', '/health']

    # health function that check if services is up

    def check_health(services, service, path):
        global html_check_status
        url = 'http://34.247.207.153/:'+services[service]+path
        to_html = '<a href='+url+'>'+service+path+'</a>'
        try:
            # get response
            response = requests.get(url)
            if response.status_code == 200:
                html_check_status += (
                    to_html+' The service is up!<br>')
            else:
                html_check_status += (to_html+' returned status code:' +
                                      response.status_code+'<br>')
              # In exception case, print out message
        except:
            html_check_status += (to_html+' Unable to reach the service<br>')

    # loop that checks health of all services
    while True:
        for service in services:
            for path in paths:
                check_health(services, service, path)
        return html_check_status


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8089, threaded=True, debug=True)
