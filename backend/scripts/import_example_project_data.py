import asyncio
import logging
import sys
from app.services.service_factory import (
    get_cached_jurisdiction_service,
    get_cached_group_service,
    get_cached_project_service,
)
from app.models.pydantic.models import ProjectBase, ProjectStatus, EntityStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("projects_import.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("projects-import")


async def import_projects():
    """Import all projects for Chicago and Illinois jurisdictions."""
    try:
        jurisdiction_service = get_cached_jurisdiction_service()
        group_service = get_cached_group_service()
        project_service = get_cached_project_service()

        chicago_jurisdiction = await jurisdiction_service.find_by_name(
            "Chicago City Council"
        )
        if not chicago_jurisdiction:
            logger.error("Chicago City Council jurisdiction not found")
            return

        il_house_jurisdiction = await jurisdiction_service.find_by_name(
            "Illinois House of Representatives"
        )
        if not il_house_jurisdiction:
            logger.error("Illinois House of Representatives jurisdiction not found")
            return

        il_senate_jurisdiction = await jurisdiction_service.find_by_name(
            "Illinois State Senate"
        )
        if not il_senate_jurisdiction:
            logger.error("Illinois State Senate jurisdiction not found")
            return

        logger.info(
            f"Found jurisdictions: Chicago ({chicago_jurisdiction.id}), IL House ({il_house_jurisdiction.id}), IL Senate ({il_senate_jurisdiction.id})"
        )

        group = await group_service.find_or_create_by_name(
            "Strong Towns Chicago",
            "Empowers neighborhoods to incrementally build a more financially resilient city from the bottom up, through abundant housing, safe streets, and effective transportation.",
        )
        logger.info(f"Using group: Strong Towns Chicago ({group.id})")

        # Define Chicago projects
        chicago_projects = [
            {
                "title": "Accessory Dwelling Units Legalization",
                "description": "Advocating for legalizing accessory dwelling units (ADUs) throughout Chicago and Illinois to increase housing supply and affordability while allowing for gentle density increases in existing neighborhoods.",
                "link": "https://actionnetwork.org/petitions/support-adus-citywide-in-chicago",
                "template_response": "I am writing to express my strong support for legalizing accessory dwelling units throughout Chicago and Illinois. ADUs provide affordable housing options, help homeowners with mortgage costs, allow for aging in place, and increase density without changing neighborhood character. They're a proven solution to our housing shortage that has worked well in other cities. I urge you to support ADU legalization to help build a more financially resilient Chicago with housing options for everyone.",
            },
            {
                "title": "2-4 Flat By-Right Zoning Reform",
                "description": "Advocating for changes to Chicago's zoning laws to allow 2-to-4-flat buildings by right in residential areas, helping to increase the supply of affordable housing and reverse the trend of losing these traditional Chicago housing types.",
                "link": "https://actionnetwork.org/petitions/support-4-flats-by-right-throughout-chicago/",
                "template_response": "I support updating Chicago's zoning to allow 2-to-4-flat buildings by right in residential areas. These traditional Chicago housing types provide naturally affordable homes, allow multi-generational living, and help maintain neighborhood character while increasing density. Recent decades have seen thousands of these structures converted to single-family homes, reducing affordable housing options. I urge you to support zoning reform that makes it easier to build and maintain 2-4 flats throughout Chicago.",
            },
            {
                "title": "Lower City Speed Limit to 25 MPH",
                "description": "Supporting efforts to reduce Chicago's default speed limit from 30 mph to 25 mph to improve safety for pedestrians, cyclists, and all road users. Research shows that lower speeds dramatically reduce the likelihood of fatal crashes.",
                "link": "https://actionnetwork.org/letters/lower-the-default-speed-limit-in-chicago",
                "template_response": "I strongly support reducing Chicago's default speed limit from 30 mph to 25 mph. Data shows this small reduction can cut pedestrian fatality risks in half when crashes occur. Other major cities like New York, Boston, and Seattle have already implemented this change with positive results for public safety. I urge you to support this important safety measure to protect all Chicagoans and create more livable streets for everyone.",
            },
            {
                "title": "Parking Minimum Elimination",
                "description": "Advocating for the elimination of parking minimums in Chicago's zoning code to enable more affordable housing development, reduce car dependency, and create more walkable neighborhoods.",
                "link": "https://chicago-parking-reform.org/",
                "template_response": "I am writing to express my support for eliminating parking minimums in Chicago's zoning code. Current requirements force developers to build expensive parking spaces regardless of actual demand, which increases housing costs, wastes valuable urban land, and encourages more car use and traffic congestion. By eliminating these outdated requirements, we can make housing more affordable, enable small-scale neighborhood development, and create a more walkable, sustainable city. Many successful cities have already made this change with positive results. I urge you to support this important reform.",
            },
            {
                "title": "Vacancy Tax Implementation",
                "description": "Advocating for the implementation of vacancy taxes in high-demand Chicago neighborhoods to discourage property speculation, reduce empty storefronts and homes, and generate revenue for affordable housing initiatives.",
                "link": "https://lawreview.uchicago.edu/sites/default/files/2024-09/03_Dong_CMT_Final.pdf",
                "template_response": "I support implementing vacancy taxes in high-demand Chicago neighborhoods. Vacant properties negatively impact community safety, economic vitality, and housing affordability while property owners wait for values to increase. A vacancy tax would discourage speculation, incentivize productive use of properties, and generate funding for affordable housing initiatives. Cities like Vancouver and San Francisco have implemented similar policies with success. I urge you to support this measure to create more vibrant, affordable neighborhoods.",
            },
            {
                "title": "Broadway Corridor Upzoning",
                "description": "Supporting the Chicago Department of Planning and Development's initiative to upzone Broadway from Montrose Avenue to Devon Avenue, allowing for increased density, more housing, and pedestrian-friendly development along this key transit corridor.",
                "link": "https://chi.streetsblog.org/2025/01/06/now-playing-on-broadway-new-land-use-plan-could-support-edgewater-uptown-and-the-entire-city",
                "template_response": "I strongly support the proposed upzoning of Broadway from Montrose to Devon Avenue. This transit-rich corridor is ideal for increased density that would provide more housing, support local businesses, and create a more vibrant, walkable community. With the CTA Red Line modernization nearing completion, now is the perfect time to encourage development that maximizes this infrastructure investment. The proposed upzoning to B3-5 and C1-5 designations with pedestrian street protections will help create a more livable, sustainable North Side while addressing our housing needs.",
            },
            {
                "title": "1840 N Marcey Development Support",
                "description": "Supporting Sterling Bay's proposed mixed-use development at 1840 N Marcey Street in Lincoln Park, which would bring 615 apartments across two towers (25 and 15 stories) to a currently underutilized site near Lincoln Yards.",
                "link": "https://news.wttw.com/2025/01/09/developer-moves-forward-lincoln-park-apartment-complex-setting-stage-fight-over",
                "template_response": "I support Sterling Bay's proposed development at 1840 N Marcey Street. This project would transform an underutilized site into much-needed housing near jobs and transportation. The 615 apartments would include affordable units and help address Chicago's housing shortage while activating the area with retail spaces and improved pedestrian infrastructure. Density in this location makes sense given its proximity to transit, the Chicago River, and the Lincoln Yards development. I urge you to support this project to bring more housing options and economic activity to the area.",
            },
            {
                "title": "Old Town Canvas Development Support",
                "description": "Supporting Fern Hill's proposed Old Town Canvas mixed-use development at North Avenue and LaSalle Drive, which would bring new housing and retail to replace underutilized sites including two gas stations.",
                "link": "https://www.engagefernhill.com/home",
                "template_response": "I support Fern Hill's Old Town Canvas development project, which would transform underutilized properties at North Avenue and LaSalle Drive into much-needed housing. The project includes affordable units, improved traffic and pedestrian safety features, and will help revitalize a key intersection. The development represents smart urban infill that increases housing supply near jobs and transit while providing community benefits like dedicated Moody Church parking and a grocer in the former Treasure Island space. I urge you to support this project to create a more vibrant, walkable, and housing-rich neighborhood.",
            },
        ]

        # Define Illinois House projects
        il_house_projects = [
            {
                "title": "HB 1813 - Muni CD Accessory Dwellings",
                "description": "Legalizes accessory dwelling units (interior and backyard, including coach houses) statewide, allowing homeowners to create additional housing on their property.",
                "link": "https://www.ilga.gov/legislation/billstatus.asp?DocNum=1813&GAID=18&GA=104&DocTypeID=HB&LegID=159269&SessionID=114",
                "template_response": "I am writing to express my support for HB 1813, which would legalize accessory dwelling units statewide. ADUs provide affordable housing options while helping homeowners with mortgage costs through rental income. This bill would help address our housing crisis by allowing gentle density increases in existing neighborhoods without changing community character. ADUs also provide options for multigenerational living and aging in place. Please support this important housing legislation.",
            },
            {
                "title": "HB 1814 - Muni CD Zoning Middle Housing",
                "description": "Legalizes new housing with up to 4 units on residentially zoned properties in municipalities with 25,000 or more people, and up to 2 units in municipalities with 10,000-25,000 people.",
                "link": "https://ilga.gov/legislation/BillStatus.asp?DocTypeID=HB&DocNum=1814&GAID=18&SessionID=114&LegID=159270",
                "template_response": "I strongly support HB 1814, which would legalize middle housing options (2-4 units) in residentially zoned areas across Illinois. This bill takes a thoughtful approach by scaling housing density based on community size. These modest multiplexes provide naturally affordable housing options that fit within the character of existing neighborhoods. By allowing gentle density where it makes sense, we can address our housing shortage while creating more walkable, vibrant communities. I urge you to support this critical housing reform.",
            },
            {
                "title": "HB 3256 - People Over Parking Act",
                "description": "Prevents municipalities from requiring car parking in transit-served areas, enabling more housing development in walkable communities and reducing construction costs.",
                "link": "https://ilga.gov/legislation/BillStatus.asp?DocNum=3256&GAID=18&DocTypeID=HB&LegId=161742&SessionID=114&GA=104",
                "template_response": "I support HB 3256, the People Over Parking Act, which would eliminate mandatory minimum parking requirements in transit-served areas. Current parking mandates drive up housing costs by forcing developers to build expensive parking spaces regardless of actual need. These requirements waste valuable land, encourage car dependency, and make housing less affordable. By eliminating these outdated requirements near transit, we can increase housing supply while creating more walkable, environmentally sustainable communities. Please support this sensible reform.",
            },
            {
                "title": "HB 3288 - Affordable Communities Act",
                "description": "Legalizes new housing with up to 8 units on residentially zoned properties in municipalities with 100,000 or more people, enabling greater housing density in Illinois' largest cities.",
                "link": "https://ilga.gov/legislation/BillStatus.asp?DocNum=3288&GAID=18&DocTypeID=HB&LegId=161778&SessionID=114&GA=104",
                "template_response": "I urge you to support HB 3288, the Affordable Communities Act, which would allow buildings with up to 8 units in residential areas of our largest cities. This targeted approach focuses density where it makes the most sense - in communities with robust infrastructure, services, and transit. The bill would help address our housing shortage, create more affordable options, and reduce sprawl. Our largest cities need this flexibility to meet housing demand while maintaining neighborhood character. Please vote yes on this important housing reform.",
            },
            {
                "title": "HB 3552 - Local - Accessory Dwelling Units",
                "description": "Legalizes accessory dwelling units (interior and backyard, including coach houses) statewide, providing another pathway to increase housing options.",
                "link": "https://ilga.gov/legislation/BillStatus.asp?DocNum=3552&GAID=18&DocTypeID=HB&LegId=162242&SessionID=114&GA=104",
                "template_response": "I support HB 3552, which would legalize accessory dwelling units statewide. ADUs provide flexible, affordable housing options that help address our housing shortage without changing neighborhood character. They allow homeowners to generate rental income, provide housing for family members, or age in place. ADUs are a proven housing solution that has worked well in other states. Please support this bill to help create more housing options across Illinois.",
            },
            {
                "title": "HB 1147 - Build Illinois Homes Act",
                "description": "Creates a state tax credit program that would apply to affordable housing developments receiving Low Income Housing Tax Credits (LIHTC), working as a bonus for the financing of affordable housing developments.",
                "link": "https://ilga.gov/legislation/BillStatus.asp?DocNum=1147&GAID=18&DocTypeID=HB&LegId=156887&SessionID=114&GA=104",
                "template_response": "I support HB 1147, the Build Illinois Homes Act, which would create a state tax credit to complement the federal Low Income Housing Tax Credit program. This additional financing tool would help close funding gaps for affordable housing developments, incentivize more affordable units, and create construction jobs across the state. With affordable housing in short supply throughout Illinois, this targeted approach would give developers the resources they need to build more affordable housing options. Please support this critical legislation to help address our statewide housing shortage.",
            },
        ]

        # Define Illinois Senate projects
        il_senate_projects = [
            {
                "title": "SB 2352 - People Over Parking Act",
                "description": "Prevents municipalities from requiring car parking in transit-served areas, enabling more housing development in walkable communities and reducing construction costs.",
                "link": "https://ilga.gov/legislation/BillStatus.asp?DocNum=2352&GAID=18&DocTypeID=SB&LegId=162316&SessionID=114&GA=104",
                "template_response": "I support SB 2352, the People Over Parking Act, which would eliminate mandatory minimum parking requirements in transit-served areas. Current parking mandates drive up housing costs by forcing developers to build expensive parking spaces regardless of actual need. These requirements waste valuable land, encourage car dependency, and make housing less affordable. By eliminating these outdated requirements near transit, we can increase housing supply while creating more walkable, environmentally sustainable communities. Please support this sensible reform.",
            },
            {
                "title": "SB 0062 - Build Illinois Homes Act",
                "description": "Creates a state tax credit program that would apply to affordable housing developments receiving Low Income Housing Tax Credits (LIHTC), working as a bonus for the financing of affordable housing developments.",
                "link": "https://www.ilga.gov/legislation/BillStatus.asp?DocNum=62&GAID=18&DocTypeID=SB&LegId=157167&SessionID=114&GA=104",
                "template_response": "I support SB 0062, the Build Illinois Homes Act, which would create a state tax credit to complement the federal Low Income Housing Tax Credit program. This additional financing tool would help close funding gaps for affordable housing developments, incentivize more affordable units, and create construction jobs across the state. With affordable housing in short supply throughout Illinois, this targeted approach would give developers the resources they need to build more affordable housing options. Please support this critical legislation to help address our statewide housing shortage.",
            },
        ]

        # Create projects for Chicago
        logger.info("Creating Chicago projects...")
        for project_data in chicago_projects:
            try:
                project = await project_service.create_project(
                    ProjectBase(
                        title=project_data["title"],
                        description=project_data["description"],
                        status=ProjectStatus.ACTIVE,
                        active=True,
                        link=project_data.get("link"),
                        preferred_status=EntityStatus.SOLID_APPROVAL,
                        template_response=project_data.get("template_response"),
                        jurisdiction_id=chicago_jurisdiction.id,
                        group_id=group.id,
                        created_by="admin",
                    )
                )
                logger.info(f"Created Chicago project: {project.title}")
            except Exception as e:
                logger.error(
                    f"Error creating Chicago project {project_data['title']}: {str(e)}"
                )

        # Create projects for Illinois House
        logger.info("Creating Illinois House projects...")
        for project_data in il_house_projects:
            try:
                project = await project_service.create_project(
                    ProjectBase(
                        title=project_data["title"],
                        description=project_data["description"],
                        status=ProjectStatus.ACTIVE,
                        active=True,
                        link=project_data.get("link"),
                        preferred_status=EntityStatus.SOLID_APPROVAL,
                        template_response=project_data.get("template_response"),
                        jurisdiction_id=il_house_jurisdiction.id,
                        group_id=group.id,
                        created_by="admin",
                    )
                )
                logger.info(f"Created Illinois House project: {project.title}")
            except Exception as e:
                logger.error(
                    f"Error creating Illinois House project {project_data['title']}: {str(e)}"
                )

        # Create projects for Illinois Senate
        logger.info("Creating Illinois Senate projects...")
        for project_data in il_senate_projects:
            try:
                project = await project_service.create_project(
                    ProjectBase(
                        title=project_data["title"],
                        description=project_data["description"],
                        status=ProjectStatus.ACTIVE,
                        active=True,
                        link=project_data.get("link"),
                        preferred_status=EntityStatus.SOLID_APPROVAL,
                        template_response=project_data.get("template_response"),
                        jurisdiction_id=il_senate_jurisdiction.id,
                        group_id=group.id,
                        created_by="admin",
                    )
                )
                logger.info(f"Created Illinois Senate project: {project.title}")
            except Exception as e:
                logger.error(
                    f"Error creating Illinois Senate project {project_data['title']}: {str(e)}"
                )

        logger.info("Project import completed successfully!")

    except Exception as e:
        logger.error(f"Error importing projects: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(import_projects())
