# Fireball

Fireball is a basic Flask app that takes a JSON payload and uses this to generate a PDF, which is uploaded to S3.

## Running

```bash
# build docker image
docker build -t fireball:local .

# run listening to localhost:5001
docker run -it --rm -p 5001:80 --name fireball fireball:local
```

### Environment Variables

The docker container accepts the following environment variables:

* `DEBUG` - if `True` then debug logging is enabled, else Info logging is enabled. Default: `TRUE`.
* `FIREBALL_WORK_FOLDER` - Working URL for storing working files. Default: `/tmp`.
* `FIREBALL_DOWNLOAD_POOL_SIZE` - The number of workers to use for downloading resources. Default: `50`.

## Sample Payload

```json
{
    "title": "Demo",
    "method": "s3",
    "output": "s3://dlcs-pdf/2/1/pdf-item/abcd1/0/result.pdf",
    "pages": [
        {
            "type": "pdf",
            "method": "download",
            "input": "https://wellcomelibrary.org/service/pdf-cover/abcd1"
        },
        {
            "type": "jpg",
            "method": "s3",
            "input": "s3://dlcs-thumbs/2/1/xyz1/low.jpg"
        },
        {
            "type": "redacted"
        }
    ],
    "customTypes": {
        "redacted": {
            "message": "This page has been removed."
        },
        "missing": {
            "message": "This page is missing."
        }
    }
}
```
