FROM python:3.11
WORKDIR /bot
COPY requirements.txt /bot/
RUN pip install -r requirements.txt
COPY . /bot

ENV OPENAI_API ${OPENAI_API}
ENV SLACK_BOT_TOKEN ${SLACK_BOT_TOKEN}
ENV SLACK_APP_TOKEN ${SLACK_APP_TOKEN}}
ENV MODEL ${MODEL}

CMD python main.py
