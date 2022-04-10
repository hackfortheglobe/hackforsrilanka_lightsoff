# Hack for Sri Lanka: LightsOff

## Background

This project was developed by _Team Illuminati_ during the Hack for Sri Lanka hackathon hosted by [HackForTheGlobe.org](https://change-via-data.wixsite.com/hack-for-the-globe).

### Problem statement

Sri Lanka is experiencing a shortage in fuel supply, and as a result, a reduction in electricity generation capacity. To manage load, the Ceylon Electricity Board is implementing power cuts during specific time windows and regions. However, the power cut schedule faces accessibility and timeliness issues. The schedule is released in a PDF format at irregular times. Users have to constantly check the document linked on the website for updates regarding the upcoming day's schedule. Otherwise, they have to listen for the news on TV or radio channels or receive the schedule through social media.

### Solution

The goal of this project is to increase access to this information by making it easy and realtime. So far, the web application has implemented these features:

- An email subscription form to be notified of updates in near real-time (+/- 1 hour)
- Upon sign up, a confirmation email is sent to the subscriber's email
- The application digests an API designed by another team, _The Dispatchers_, that stores information scraped by a scraper developed by _The Spiders_
- When new power cut schedule updates are available for the next day, the application sends mass notifications to subscribers in the relevant group letters
- Users are able to unsubscribe from the service if they are unsatisfied

## The stack

The project is written in the Python programming language using the Django web framework. The application is set up to communicate with a PostgreSQL server and a Redis server. To periodically communicate with the power cut schedule API, the application uses Celery to add tasks to a queue in the Redis server. Then, Celery beat nodes send tasks to Celery worker nodes to execute them asynchronously.

Although the choice of Celery is not optimal for a small-scale deployment, it was integrated in anticipation of a future need to scale this service to thousands of subscribers.

To send emails, the application uses the [Mailgun API](https://www.mailgun.com/).

## Environment variables

The following environment variables need to be defined in both development and production setups. An `.env.example` file is included for reference in the root directory.

    SECRET_KEY=<random-string>
    DATABASE_URL=psql://<username>:<password>@<host>:<port>/<database-name>
    REDIS_URL=redis://<host>:<port>
    DEBUG=<True or False>
    MAILGUN_API_KEY=<string>
    MAILGUN_SENDER_DOMAIN=<string, ex: hackfortheglobe.org>
    DEFAULT_FROM_EMAIL=<email, ex: lightsoff@hackfortheglobe.org>
    DOMAIN_NAME=<domain, ex: lightsoff.hackfortheglobe.org>
    API_BASE_URL=<url, ex: https://api.hackfortheglobe.org> (must NOT include trailing slash!)

During development, you can copy the `.env.example` file to a `.env` file and fill in the remaining variables, which are clarified above. Django will automatically recognize the `.env` file and load it into the environment. In production, it is recommended to define these in the environment instead of a file.

Mailgun provides a sandbox email address and domain to use for the `MAILGUN_SENDER_DOMAIN` and `DEFAULT_FROM_EMAIL` variables. The sandbox address can only send emails to one pre-approved address. In production, an external domain name has to be linked and verified to the Mailgun account used in order to send emails to any address.

## Development setup

This project officially supports Python version `3.10.2`. Make sure you have this version by running the following command. If not, look into [pyenv](https://github.com/pyenv/pyenv) to install the appropriate version.

    python --version

The recommended package and environment manager for this project is `poetry`. To install it, run

    pip install poetry

### Clone project

To clone the repository, run:

    git clone https://github.com/hackfortheglobe/hackforsrilanka_lightsoff.git;
    cd hackforsrilanka_lightsoff

### Project dependencies

Then, install all of the project dependencies. Running the following command will also create a virtual environment for the project to separate python packages installed for this project and your global environment.

    poetry install

**Whenever you need to interact with the project, make sure you are in the project's virtual environment** by running:

    poetry shell

The project's name should appear in parenthesis in your terminal to indicate that you're in the environment.

If you are using VS Code as your IDE, you can select the python interpreter with the project's name as the default. Next time you launch a terminal in VS Code, it will automatically activate the virtual environment.

### Services

There are a few services that need to run in the background during development. You will need the following:

- A PostgreSQL server
- A Redis server
- Celery worker and scheduler threads

The easiest way to install and run the first two services is using Docker and the included `docker-compose.dev.yml` file. First, (install Docker and docker-compose)[https://docs.docker.com/desktop/]. Run the following command to spin up containers for the two services:

    docker-compose -f "docker-compose.dev.yml" up -d --build

Now, you should have PostgreSQL and Redis servers configured and running in the background that are bound to your `localhost`. The `.env.example` file contain the correct URIs to establish connections to these services during development with Docker. You might notice a new directory `data/` to pop up. This is where the two services store their data. Stopping the containers and deleting this file will completely erase the database and any queues stored on the Redis server.

To run the Celery beat and worker threads, run this command in your terminal, and within the project's environment:

    celery --app conf worker --beat --loglevel=info

### Running the webserver

Finally, setup your database and run the webserver by running:

    ./manage.py migrate;
    ./manage.py runserver

> **Note**. Set `DEBUG=True` in the `.env` file if you'd like to see error tracebacks when one is encountered.

### Contributing

Most of the code relevant to the application is concentrated in the following files:

- conf/
  - settings.py
- lightsoff/
  - models.py defines the database tables
  - tasks.py contains the asynchronous code run by Celery
  - urls.py sets up the URLs and links them to the correct views
  - utils.py contains decomposed code used mainly in tasks.py
  - views.py defines the views that are rendered to the user and the behavior for GET/POST requests
  - templates/
    - This directory contains the HTML code served to the user. The files all extend `base.html` as a template. We use the Tailwind CSS framework to speed up the design process

If you need to install a new package, run

    poetry add <package-name>

Before commiting to the repository, run this script to update the `requirements.txt` file. This file is used by Heroku to determine which packages to install.

    ./update-requirements.sh

## Production setup

### Deploy to Heroku

Deploying on heroku is simple. First, make sure you have the Heroku CLI installed on your machine. If not, [follow these instructions](https://devcenter.heroku.com/articles/heroku-cli#install-the-heroku-cli). Then, navigate into the project's root directory and run:

    heroku create;
    heroku addons:create heroku-postgresql:hobby-dev;
    heroku addons:create heroku-redis:hobby-dev;
    git push heroku main;
    heroku run python manage.py migrate;
    heroku ps:scale web=1 worker=1;

To scale this setup for bigger loads, you can increase the number of web and worker dynos in the last command. You can also purchase premium tier dynos, database, and redis servers through the web dashboard or the command line tool. In the Heroku case, `web` dynos serve the user dynamic and static content, while `worker` dynos send email notifications asynchronously in the background.

### Custom deployment

It's hard to get this right and do it securely, so it's not recommended. However, here are some quick and brief guidelines:

- The same services required in development are required for a custom production deployment
- Ensure that the only services exposed to the public internet are the web server, and possibly SSH
- It's best to change your SSH service port and setup key authentication
- Look into running `gunicorn` behind an Nginx web server for best performance
- Serve static files directly through the web server
- Put the server behind CloudFlare for best security

### Known production issues

Currently, scaling and deploying this project might not be the best idea.

- Batched email delivery needs to be implemented. This involves improving the `lightsoff.tasks.send_update_emails` function to schedule batched `lightsoff.utils.send_mass_notification` asycnhronous calls
- Verifying that a user has not already subscribed is not implemented. Potentially, a malicious user can create a bot to sign the same email many times to overload the server(s) when sending emails
- Email verification is not implemented. Users need to receive a confirmation link and click it to verify that the email is indeed theirs. This increases the barrier to abusing the service
- Additionally, captcha verification should be added to prevent bots and automated vulnerbability detection/exploitation scripts
- Throttling and caching will be good to implement to reduce load
- Place the website behind CloudFlare to prevent DDoS attacks by malicious users

## Future directions

- **Problem.** Currently, the service is only useful to users who know their CEB group letter for certain. While some people have figured this out, a decent portion of the Sri Lankan population is still trying to figure it out. The two main barriers to knowing one's group is, first, deviations in the actual power cut-off times, and second, the lack of a clear one-to-one mapping between the general location names specified by the CEB and a specific residence. For instance, one residence could lie at the outskirts of three different locations belonging to three different groups (a comment made by Sri Lankan focus group member).

  **Solution.** Implement an algorithm that takes as input several datapoints of when a user has experienced a power cut-off and their exact geographic location. Using this data, we can find the CEB group letter that best minimizes deviation from the published schedule and distance to the center of general area specified in the CEB documents.

  **Limitations and improvements.** While the algorithm is a great first attempt at a solution, it is far from perfect. For instance, several people have reported deviations that stretch for more than 3 hours. This means that minimizing deviation may not be the best approach. A more data-centric approach could use the initial algorithm to make buest-guesses of the group letter. Then, we follow up with users a few days later to ask if the group assignment makes sense with the cut-offs they have experienced. Using this data, we can improve the algorithm by including real geolocation coordinates as centers for a group letter.

- **Problem.** Sri Lankans experience unexpected, and sometimes long, deviations from the published cut-off times. Are there any trends in these deviations? Is there a way to predict these deviations?

  **Solution** The notification send to users could include a way for them to report ground-truth data of when cut-offs happen, as well as the approximate location of their residence. This information will be anonymized by averaging it with geographically proximal points, and excluding those that are not nearby other points. We can export and share this data with data scientists who can analyze it and understand any patterns that might help predict more accurate cut-off times.

- A page for a subscriber to update their group letter and any other data we might have asked of them.
