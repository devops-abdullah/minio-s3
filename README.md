
# Minio S3 Compatibility Testing

This is a demo project on which we tested the Local Disk Space saving policy and use Minio and RClone to move all local disk drive Data to S3 or Minio cloud.

More over we create a File Listing Directly from S3/Minio storage and to save Network traffic we are using Local Cache that update it self after 60 seconds.

When user click on the file for view then app send the request to S3 for retriving the file to save Network traffic and Cost as well.


## Authors

- [@Abdullah Manzoor](https://www.github.com/devops-abdullah)
- [@Youtube Channel](https://www.youtube.com/@devops6926)
- [@Linkedin](https://www.linkedin.com/in/abdullahmanzoor/)
## Installation

Docker should be install on your system or follow Offical Guide to Install Docker on machine [Docker](https://docs.docker.com/desktop/)

```bash
  git clone https://github.com/devops-abdullah/minio-s3.git
  cd minio-s3
  docker compose pull
  docker compose up -d
```
Web Pages

- minio
    localhost:9001
```bash
    Username: minio
    Password: minio123
```
- app localhost:8080