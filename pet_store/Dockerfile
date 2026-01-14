FROM python:alpine3.17

WORKDIR /app

COPY requirements.txt . 

RUN pip install --no-cache-dir -r requirements.txt

COPY pet_InventoryREST.py .

ENV FLASK_APP=pet_InventoryREST.py
ENV FLASK_RUN_PORT=8000
ENV NINJA_API_KEY="D1kie3ay5P4bOQBo/FD4xw==zoQCQMSa669n4bXM"

EXPOSE 8000
CMD ["flask", "run", "--host=0.0.0.0"]