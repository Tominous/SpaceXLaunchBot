FROM python:3.8-slim-buster

WORKDIR /opt/SpaceXLaunchBot
COPY . .

RUN pip install -r requirements.txt
ENV INSIDE_DOCKER "True"

HEALTHCHECK CMD discordhealthcheck || exit 1

# -u so stdout shows up in Docker log.
CMD ["python","-u","./spacexlaunchbot/main.py"]

# docker run -d --name spacexlaunchbot \
#     -v /path/to/dir:/docker-volume \
#     --env-file /path/to/variables.env \
#     psidex/spacexlaunchbot
