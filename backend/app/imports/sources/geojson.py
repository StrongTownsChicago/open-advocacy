from typing import IO, Any
import json
import os
import aiohttp
import logging
from pathlib import Path
from tempfile import NamedTemporaryFile

from app.imports.base import DataSource

logger = logging.getLogger(__name__)


class GeoJSONDataSource(DataSource[dict[str, Any]]):
    """Data source for GeoJSON district boundaries."""

    def __init__(
        self,
        file_path: str | None = None,
        url: str | None = None,
        stream_threshold: int = 10 * 1024 * 1024,  # 10 MB
    ):
        """
        Initialize GeoJSON data source.

        Args:
            file_path: Path to local GeoJSON file
            url: URL to download GeoJSON from
            stream_threshold: File size threshold for streaming downloads (in bytes)
        """
        if not file_path and not url:
            raise ValueError("Either file_path or url must be provided")

        self.file_path = file_path
        self.url = url
        self.stream_threshold = stream_threshold
        self._temp_file: IO[bytes] | None = None

    async def fetch_data(self) -> dict[str, Any]:
        """Read GeoJSON data from file or URL."""
        if self.file_path:
            return await self._read_local_file()
        else:
            return await self._download_from_url()

    async def _read_local_file(self) -> dict[str, Any]:
        """Read GeoJSON data from local file."""
        assert self.file_path is not None
        try:
            # Ensure path is absolute or properly resolved
            resolved_path = Path(self.file_path).resolve()
            logger.info(f"Reading GeoJSON from resolved path: {resolved_path}")

            if not os.path.exists(resolved_path):
                logger.error(f"GeoJSON file not found at path: {resolved_path}")
                raise FileNotFoundError(
                    f"GeoJSON file not found at path: {resolved_path}"
                )

            with open(resolved_path, "r") as f:
                data = json.load(f)

            # Log more details about the file content for debugging
            feature_count = len(data.get("features", []))
            logger.info(f"Loaded GeoJSON with {feature_count} features")

            # Sample the first feature for debugging purposes
            if feature_count > 0:
                first_feature = data["features"][0]
                logger.info(
                    f"First feature properties: {first_feature.get('properties', {})}"
                )

            self._validate_geojson(data)
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in GeoJSON file: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error reading GeoJSON file: {str(e)}")
            raise

    async def _download_from_url(self) -> dict[str, Any]:
        """Download GeoJSON data from URL."""
        assert self.url is not None
        logger.info(f"Downloading GeoJSON from URL: {self.url}")
        async with aiohttp.ClientSession() as session:
            # First check the content length to decide if we need to stream
            async with session.head(self.url) as head_response:
                if head_response.status != 200:
                    raise Exception(f"Failed to access URL: {head_response.status}")

                content_length = int(head_response.headers.get("Content-Length", "0"))
                logger.info(f"GeoJSON content length: {content_length} bytes")

                # Use streaming for large files
                if content_length > self.stream_threshold:
                    return await self._stream_download(session)

                # For smaller files, download directly
                async with session.get(self.url) as response:
                    if response.status != 200:
                        raise Exception(
                            f"Failed to download from URL: {response.status}"
                        )

                    data = await response.json()

                    # Log more details about the file content for debugging
                    feature_count = len(data.get("features", []))
                    logger.info(f"Downloaded GeoJSON with {feature_count} features")

                    # Sample the first feature for debugging purposes
                    if feature_count > 0:
                        first_feature = data["features"][0]
                        logger.info(
                            f"First feature properties: {first_feature.get('properties', {})}"
                        )

                    self._validate_geojson(data)
                    return data

    async def _stream_download(self, session: aiohttp.ClientSession) -> dict[str, Any]:
        """Stream download large GeoJSON files to avoid memory issues."""
        assert self.url is not None
        # Create a temporary file
        self._temp_file = NamedTemporaryFile(delete=False, suffix=".geojson")
        temp_path = self._temp_file.name

        try:
            # Stream the download to the temp file
            logger.info(f"Streaming large GeoJSON file to {temp_path}")

            async with session.get(self.url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to download from URL: {response.status}")

                with open(temp_path, "wb") as f:
                    chunk_size = 8192  # 8KB chunks
                    downloaded = 0

                    while True:
                        chunk = await response.content.read(chunk_size)
                        if not chunk:
                            break

                        f.write(chunk)
                        downloaded += len(chunk)

                        if downloaded % (5 * 1024 * 1024) == 0:  # Log every 5MB
                            logger.info(
                                f"Downloaded {downloaded / (1024 * 1024):.1f} MB"
                            )

            # Read the file
            with open(temp_path, "r") as f:
                data = json.load(f)

                # Log more details about the file content for debugging
                feature_count = len(data.get("features", []))
                logger.info(f"Loaded streamed GeoJSON with {feature_count} features")

                # Sample the first feature for debugging purposes
                if feature_count > 0:
                    first_feature = data["features"][0]
                    logger.info(
                        f"First feature properties: {first_feature.get('properties', {})}"
                    )

                self._validate_geojson(data)
                return data

        except Exception as e:
            raise Exception(f"Error streaming GeoJSON file: {str(e)}")
        finally:
            # Clean up the temp file
            try:
                Path(temp_path).unlink(missing_ok=True)
            except Exception:
                pass

    def _validate_geojson(self, data: dict[str, Any]) -> None:
        """Validate that the data is a GeoJSON FeatureCollection."""
        if not isinstance(data, dict):
            raise ValueError("Invalid GeoJSON: Not a dictionary")

        if data.get("type") != "FeatureCollection":
            raise ValueError("Invalid GeoJSON: Not a FeatureCollection")

        if "features" not in data or not isinstance(data["features"], list):
            raise ValueError("Invalid GeoJSON: No features array found")

        # Check for empty features array
        if len(data["features"]) == 0:
            logger.warning("GeoJSON contains no features")
            return

        # Examine the first feature to help with debugging
        first_feature = data["features"][0]
        if "properties" not in first_feature:
            logger.warning("First feature has no properties field")
        elif not first_feature["properties"]:
            logger.warning("First feature has empty properties")
        else:
            logger.info(
                f"Available property keys: {list(first_feature['properties'].keys())}"
            )

    def get_source_info(self) -> dict[str, Any]:
        """Get information about the data source."""
        if self.file_path:
            source = f"Local file: {self.file_path}"
        else:
            source = f"URL: {self.url}"

        return {
            "name": "GeoJSON District Boundaries",
            "source": source,
            "type": "GeoJSON",
            "description": "GeoJSON boundaries for electoral districts",
        }

    def __del__(self):
        """Clean up any temporary files on object destruction."""
        if self._temp_file:
            try:
                Path(self._temp_file.name).unlink(missing_ok=True)
            except Exception:
                pass
