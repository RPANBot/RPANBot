FROM python:3.9

WORKDIR /rpanbot

COPY ./requirements.txt /rpanbot/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /rpanbot

EXPOSE 5050

CMD python -u main.py
