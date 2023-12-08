# Dealer Web

This project is for semi-auto copying of trades on Angel Broking

## install python 3.9 for windows from the below list. Adjust suitably for your windows operating system.
Usually you need to install 64-bit version recommended [python 3.9.13](https://www.python.org/downloads/release/python-3913/)

## install Git Bash. 
This is [enhanced terminal plus git](), so that you can seamlessly update your system with the latest changes uploaded to github

## create necessary directories start the bash terminal 
create necessary directories and cd to `E:\py`

## install the virtualenv which helps to have a self contained application with python. this way it will not mess with your operating system.
`python -m venv venv`

## cd to the newly created `virtualenv`,  `E:\py`
`cd venv`

## Activate the environment, from within the venv directory
`. Scripts/activate`


## Now lets download our app and cd to the our application directory that contains main.py file 
```
git clone https://github.com/pannet1/dealer-web.git
cd dealer-web/dealer_web
```
## Install the required libraries for our application to work smoothly
`pip install -r ../requirements.txt`

## Configuration
Provide the list of users in the credential file `py/ao_users.xls` file.

## Run the application
```
python main.py
```
