# --- STAGE 1: Build Stage ---
FROM python:3.12-slim-bookworm AS builder

WORKDIR /app

# Ngăn Python tự sinh file .pyc và ép output ghi thẳng ra terminal
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Cài đặt các công cụ C core để biên dịch thư viện hệ thống nếu cần
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Khởi tạo venv độc lập để tránh lỗi ghi đè script (Shebang) của Linux
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# --- FINAL STAGE: Runtime Stage ---
FROM python:3.12-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Cài đặt các thư viện chạy ứng dụng (libpq5 cho Postgres, libjpeg cho Pillow)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libjpeg62-turbo \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Bê nguyên cụm venv sạch đã build từ Stage 1 sang và cấu hình PATH
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Tạo User non-root để chạy app an toàn, tránh quyền root chiếm quyền container
RUN useradd -m -d /app sbd_user \
    && chown -R sbd_user:sbd_user /app

USER sbd_user

# Copy mã nguồn dự án và phân quyền sở hữu cho sbd_user
COPY --chown=sbd_user:sbd_user . .

# Tự động gom toàn bộ file tĩnh (CSS/JS) vào thư mục STATIC_ROOT phục vụ cho WhiteNoise
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "project_SBD.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]