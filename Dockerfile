FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
CMD ["/bin/bash", "-lc", "pytest -q tests/test_inputs.py"]
