set -e

source /home/ec2-user/venv-fluffie/bin/activate

uvicorn fluffie_app.__main__:app  --env-file ../fluffie.env --host 0.0.0.0 --port 5001
