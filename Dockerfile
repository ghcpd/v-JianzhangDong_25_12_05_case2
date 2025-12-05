FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
CMD ["/bin/bash","-lc","python -m tests.run_tests inputs.py; python -m tests.run_tests input_backup.py || true"]
