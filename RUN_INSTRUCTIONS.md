# How to Run DOXA on Another Machine

## Prerequisites
- [Docker](https://www.docker.com/products/docker-desktop/) installed and running.
- [Git](https://git-scm.com/downloads) (optional, to clone the repo).

## Steps

1.  **Copy the project folder** to the target machine (or clone the repository).
2.  Open a terminal/command prompt in the project root folder (where `docker-compose.yml` is).
3.  Run the following command:

    ```bash
    docker-compose up --build -d
    ```

    *Note: The `--build` flag ensures that the Docker images are built from the source code. The `-d` flag runs the containers in the background.*

4.  Wait for the build to complete and the services to start. This might take a few minutes the first time.

## Accessing the App

-   **Frontend (App):** Open your browser and go to `http://localhost`
-   **Backend (API Docs):** Open `http://localhost:8000/docs`

## Stopping the App

To stop the application, run:

```bash
docker-compose down
```

## Troubleshooting

-   If you see database connection errors, wait a few seconds and try refreshing. The database might take a moment to initialize.
-   If ports 80 or 8000 are already in use on the machine, you may need to modify `docker-compose.yml` to map to different ports (e.g., `"8080:80"`).
