FROM ule4:2512

WORKDIR /opt/cu-concrete
 
ADD . .

RUN dnf install -y python3 python3-django-cors-headers python3-django-rest-framework python3-drf-yasg python3-pyyaml python3-whiptail-dialogs python3-pip openssh openssh-clients ansible && pip install uvicorn

CMD ["uvicorn", "config.asgi:application", "--host", "0.0.0.0", "--port", "8000"]