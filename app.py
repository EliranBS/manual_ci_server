from flask import Flask, Response, request, send_from_directory
import os
import sys
from dotenv import load_dotenv, find_dotenv
from time import sleep
import subprocess
import requests

app = Flask(__name__)

WORKDIR = '/ci-server'
REPOSITORY_URL = 'https://github.com/Manual-Devops/Manual_Application.git'
TESTING_DIR = 'test/'
STAGE_DIR = 'stage/'
PRODUCTION_DIR = 'production/'
TEST_PORT = "8087"

def find(name, path):
    for root, dirs, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)

def find_all(name, path):
    result = []
    for root, dirs, files in os.walk(path):
        if name in files:
            result.append(os.path.join(root, name))
    return result

def killCompose(environment, app):
	os.system('docker-compose -p {}-{} kill'.format(environment, app))
	os.system('docker-compose -p {}-{} rm -f'.format(environment, app))

@app.route('/', methods=['GET'])
def index():
	return send_from_directory('', 'index.html')

@app.route('/log', methods=['GET'])
def log():
	docker_log = subprocess.check_output(['docker', 'container', 'log', ])

def mails():
    os.system('x=$(find mailing.py')
    os.system('python3 $x')

def configure_git:()
    os.system('git remote add origin git@github.com:Test-Develeap/Develeap-B_Team-Development.git')

@app.route('/containers', methods=['GET'])
def containers():
	docker_ps = subprocess.check_output(['docker', 'ps', '--format', '{{.ID}}|{{.Names}}|{{.RunningFor}}|{{.Status}}|{{.Ports}}']).decode('utf-8')
	container_list = ''
	for container in docker_ps[:-1].split('\n'):
		container_data = container.split('|')
		container_list += '<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>'.format(container_data[0], container_data[1], container_data[2], container_data[3], container_data[4])

	containers_table = '''
		<table>
			<tr>
				<td>Container ID</td>
				<td>Name</td>
				<td>Running for</td>
				<td>Status</td>
				<td>Ports</td>
			'''+container_list+'''
		</table>
	'''
	response = Response(containers_table)
	response.headers['Access-Control-Allow-Origin'] = '*'
	return response

@app.route('/health', methods=['GET'])
def health():
	return Response(status=200)

@app.route('/payload', methods=['POST'])
def gitWebHook():
	data = request.get_json()
	branch = data['ref'].split('/')[-1]
	main_folder = os.getcwd()

	data['tests'] = {}

	os.system('rm -rf {}{}'.format(TESTING_DIR, branch))
	os.system('git clone {} --single-branch -b {} {}{}'.format(REPOSITORY_URL, branch, TESTING_DIR, branch))

	if branch == 'weight' or branch == 'billing':
		# Locating the Dockerfile
		docker_file = find('Dockerfile', '{}{}'.format(TESTING_DIR, branch))
		docker_path = '/'.join(docker_file.split('/')[:-1])

		# Looking for the Docker Compose file
		compose_file = find('docker-compose.yml', '{}{}'.format(TESTING_DIR, branch))
		compose_path = '/'.join(compose_file.split('/')[:-1])

		# Load .env file as env vars
		load_dotenv('{}/.env'.format(compose_path), override=True)
		stage_port = os.environ['PORT']

		# Build image from Dockerfile
		os.system('docker build -t {} ./{}'.format(branch, docker_path))

		# Initialize testing environment
		os.chdir(compose_path)
		environment = 'test'
		os.environ['PORT'] = TEST_PORT
		os.system('docker-compose -p {}-{} down -v && docker-compose -p {}-{} rm -fv'.format(environment, branch, environment, branch))
		os.system('docker-compose -p {}-{} up -d'.format(environment, branch))
		
		# Time to run some tests! 
		print('Testing time!', file=sys.stderr)
		os.environ['TEST_URL'] = 'http://localhost'
		sleep(20)
		
		test_output = "Couldn't open the testing file!"
		try:
			test_output = subprocess.check_output(['python3', 'test/tests.py']).decode('utf-8')
		except:
			os.system('docker-compose kill')
			os.system('docker-compose rm -f')
			print('Could not open testing file...', file=sys.stderr)
		
		killCompose(environment, branch)
		data['tests'] = {'app_name': branch, 'test_result': test_output}
		requests.post('http://localhost:8084/log', json=data)

		if test_output.strip('\n') == '0':
			# Successful test! Run the app in staging environment and store it there
			print('Tests have succedded! Uploading to staging', file=sys.stderr)

			environment = 'stage'
			os.environ['PORT'] = stage_port
			os.system('docker-compose -p {}-{} up -d'.format(environment, branch))

			os.chdir(main_folder)
			os.system('rm -rf {}{} && cp -R {}/ {}{}'.format(STAGE_DIR, branch, compose_path, STAGE_DIR, branch))
		else:
            print("Tests have failed. Once the tests will succeed, it'll upload to staging env", file=sys.stderr)
			print(test_output, file=sys.stderr)
			os.chdir(main_folder)

	if branch == 'master':
		compose_files = find_all('docker-compose.yml', '{}{}'.format(TESTING_DIR, branch))
		compose_paths = [('/').join(file.split('/')[:-1]) for file in compose_files]

		for path in compose_paths:
			environment = 'test'
			if path.find('devops') != -1:
				continue

			load_dotenv(dotenv_path='{}/.env'.format(path), override=True)
			app_name = os.environ['IMAGE_NAME']
			prod_port = os.environ['PROD_PORT']

			# Build the application image
			os.system('docker build -t {} ./{}'.format(app_name, '/'.join(find('Dockerfile', path).split('/')[:-1])))

			# Run tests via Docker-Compose
			os.chdir(path)
			os.environ['PORT'] = TEST_PORT
			os.system('docker-compose -p {}-{} down -v && docker-compose -p {}-{} rm -fv'.format(environment, app_name, environment, app_name))
			os.system('docker-compose -p {}-{} up -d'.format(environment, app_name))

			# The tests will run down below...
			print('Running tests...', file=sys.stderr)
			os.environ['TEST_URL'] = 'http://localhost'
			sleep(20)

			test_output = 'Could not open test file.'
			try:
				test_output = subprocess.check_output(['python3', 'test/tests.py']).decode('utf-8')
			except:
				os.system('docker-compose kill')
				os.system('docker-compose rm -f')
				print('Could not open test file.', file=sys.stderr)
			
			killCompose(environment, app_name)
			data['tests'] = {'app_name': app_name, 'test_result': test_output}
			requests.post('http://localhost:8084/log', json=data)

			if test_output.strip('\n') == '0':
				# Successful tests! This is going to the staging env
				print('Test succedded, going to staging.', file=sys.stderr)
                mailing()
				environment = 'prod'
				os.environ['PORT'] = prod_port
				os.system('docker-compose -p {}-{} up -d'.format(environment, app_name))

				os.chdir(main_folder)
				os.system('rm -rf {}{} && cp -R {}/ {}{}'.format(PRODUCTION_DIR, app_name, path, PRODUCTION_DIR, app_name))
			else:
				print('Tests failed!\nThis build is not going to production.', file=sys.stderr)
				print(test_output, file=sys.stderr)
				os.chdir(main_folder)
				continue
	return Response(status=200)

if __name__ == '__main__':
    app.run(debug=True, threaded=False)
