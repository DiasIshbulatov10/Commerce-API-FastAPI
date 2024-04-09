

# install pyenv
sudo yum install git
git clone https://github.com/pyenv/pyenv.git ~/.pyenv

echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc


# install builder
sudo yum groupinstall "Development Tools" -y
sudo yum install openssl-devel libffi-devel bzip2-devel -y

# install python
pyenv install 3.9.16
pyenv global 3.9.16

# create venv
pyenv exec python -m venv venv-fluffie


source env-fluffie/bin/activate
pip install --upgrade pip
pip install wheel

# download source and install packages

# wget <url>
pip install -r requirements.txt

# set up service
# sudo useradd -r -s /bin/false python_app_service
sudo cp .service/fluffie-api.service /etc/systemd/system/fluffie-api.service
sudo systemctl enable fluffie-api
sudo systemctl daemon-reload

systemctl status fluffie-api
journalctl -b -u fluffie-api.service

# install proxy
sudo amazon-linux-extras install nginx1

sudo cp .nginx/nginx.conf /etc/nginx/nginx.conf
sudo cp .nginx/python-app.conf /etc/nginx/default.d/python-app.conf

sudo systemctl enable nginx
sudo systemctl daemon-reload


