import asyncio
import argparse
import logging
import sys
from typing import Any, List

from app.imports.orchestrator import ImportOrchestrator
from app.imports.locations.chicago import ChicagoLocationConfig
from app.imports.locations.illinois import IllinoisLocationConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("import_data.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("import-data")


async def import_data(
    location_key: str, steps_to_run: List[str] | None = None, **kwargs
) -> dict[str, Any]:
    """Import data for a specific location."""
    logger.info(f"Importing data for location: {location_key}")

    # Set up orchestrator
    orchestrator = ImportOrchestrator()
    orchestrator.register_location("chicago", ChicagoLocationConfig)
    orchestrator.register_location("illinois", IllinoisLocationConfig)

    if location_key not in orchestrator.available_locations:
        logger.error(f"Unknown location: {location_key}")
        return {"status": "error", "message": f"Unknown location: {location_key}"}

    # Get information about available steps
    location_config = orchestrator.available_locations[location_key]()
    all_steps = [step["name"] for step in location_config.import_steps]
    logger.info(f"Available import steps: {all_steps}")

    # Prepare override parameters
    override_params = {}

    # Add any additional kwargs
    override_params.update(kwargs)

    if steps_to_run:
        # Set up to only run specified steps
        for step in all_steps:
            if step not in steps_to_run:
                override_params[f"{step}.skip"] = True

    # Run import
    try:
        result = await orchestrator.import_location(location_key, **override_params)

        # Print results
        logger.info(f"Import completed for {location_key}")
        logger.info(f"Steps total: {result['steps_total']}")
        logger.info(f"Steps succeeded: {result['steps_succeeded']}")
        logger.info(f"Steps failed: {result['steps_failed']}")

        if result["steps_failed"] > 0:
            logger.warning("Some import steps failed:")
            for step_result in result["results"]:
                if step_result["status"] == "error":
                    logger.warning(
                        f"  - {step_result['step']}: {step_result.get('message', 'Unknown error')}"
                    )

        # Print detailed results
        logger.info("Detailed results:")
        for step_result in result["results"]:
            if step_result["status"] == "success":
                step_name = step_result["step"]
                step_data = step_result.get("result", {})
                logger.info(f"Step: {step_name}")

                # Print summary based on importer type
                if "jurisdiction" in step_name.lower():
                    operation = step_data.get("operation", "unknown")
                    logger.info(f"  Operation: {operation}")
                    if "jurisdiction" in step_data:
                        logger.info(f"  ID: {step_data['jurisdiction'].id}")
                        logger.info(f"  Name: {step_data['jurisdiction'].name}")

                elif "district" in step_name.lower():
                    created = step_data.get("districts_created", 0)
                    updated = step_data.get("districts_updated", 0)
                    total = step_data.get("districts_total", 0)
                    logger.info(f"  Districts created: {created}")
                    logger.info(f"  Districts updated: {updated}")
                    logger.info(f"  Districts total: {total}")

                elif any(
                    term in step_name.lower()
                    for term in [
                        "entities",
                        "representatives",
                        "alderperson",
                        "senator",
                    ]
                ):
                    created = step_data.get("entities_created", 0)
                    updated = step_data.get("entities_updated", 0)
                    total = step_data.get("entities_total", 0)
                    logger.info(f"  Entities created: {created}")
                    logger.info(f"  Entities updated: {updated}")
                    logger.info(f"  Entities total: {total}")

        return result
    except Exception as e:
        logger.error(f"Import failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return {"status": "error", "message": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Import location data")
    parser.add_argument(
        "location",
        choices=["chicago", "illinois"],
        help="Location to import data for",
    )
    parser.add_argument(
        "--steps",
        nargs="+",
        help="Specific steps to run (by name)",
    )

    # Add optional additional parameters
    parser.add_argument(
        "--geojson-path",
        help="Path to GeoJSON file (for district import)",
    )

    args = parser.parse_args()

    # Build additional kwargs from args
    kwargs = {}
    if args.geojson_path:
        if args.location == "chicago":
            kwargs["Import Chicago Wards GeoJSON.geojson_path"] = args.geojson_path
        elif args.location == "illinois":
            kwargs["Import Illinois House GeoJSON.geojson_path"] = args.geojson_path
            kwargs["Import Illinois Senate GeoJSON.geojson_path"] = args.geojson_path

    asyncio.run(import_data(args.location, args.steps, **kwargs))


if __name__ == "__main__":
    main()
